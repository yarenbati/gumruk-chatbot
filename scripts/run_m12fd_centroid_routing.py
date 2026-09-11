"""Development-only implicit document-centroid routing experiment.

The router uses only a raw question embedding and arithmetic centroids built
from existing copied Chroma embeddings. Gold document identities are read
only after routing, for evaluation.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import statistics
import subprocess
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from openai import OpenAI

from scripts import run_m12d_three_source as m12d
from scripts.run_m12fa_explicit_law import cached_embeddings, detect_laws
from src import config, evaluate_documents as ev, retrieve

ROOT = m12d.ROOT
OUT = ROOT / "reports/evaluation/m12fd-centroid-routing"
B0_PATH = ROOT / "reports/evaluation/m12fb-candidate-pool-diagnostic.json"
HEAD = "289dd59c74e2eb22193e936bdd4d16aadbc2e8b9"
MODEL = "text-embedding-3-small"
DIMENSIONS = 1536
CUTOFFS = (1, 3, 5)
VARIANTS = ("B0", "R1", "R2")
PRIMARY = ["k5607-002", "k5607-003", "k5607-004", "k5607-025", "k5607-026", "k5607-029"]
DRIFT = ["k5607-014"]
CONTROLS = ["k5607-017", "k5607-023", "k5607-028", "k5607-030"]
DOC_IDS = tuple(m12d.DOCS.values())
PROTECTED_GLOBS = (
    "src/*.py", "app.py", "evaluation/*", "data/source_manifest.json",
    "reports/evaluation/m12d-*", "reports/evaluation/m12e-*",
    "reports/evaluation/m12fa-*", "reports/evaluation/m12fb-*",
    "reports/evaluation/m12fc-*", "scripts/run_m12d_three_source.py",
    "scripts/run_m12fa_explicit_law.py",
)


def _load() -> dict[str, Any]:
    """Load the single persisted experiment state."""
    return json.loads(OUT.with_suffix(".json").read_bytes())


def _save(state: dict[str, Any]) -> None:
    """Write deterministic UTF-8 JSON state."""
    m12d._write(OUT.with_suffix(".json"), state)


def population() -> list[ev.DocumentQuestion]:
    """Load the reviewed 105-question M12D population and verify its records."""
    questions = m12d._questions()
    saved = json.loads(m12d.JSON_PATH.read_bytes())
    assert [q.to_dict() for q in questions] == [r["question"] for r in saved["results"]]
    assert len(questions) == len({q.question for q in questions}) == 105
    assert Counter(q.expected_document_ids.__iter__().__next__() for q in questions) == Counter({
        m12d.DOCS["5326"]: 45, m12d.DOCS["4458"]: 30, m12d.DOCS["5607"]: 30})
    return questions


def _hash(path: Path) -> dict[str, Any]:
    """Hash one protected file."""
    data = path.read_bytes()
    return {"size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def _tree(path: Path) -> dict[str, Any]:
    """Hash every file under a directory."""
    files = {p.relative_to(path).as_posix(): _hash(p) for p in sorted(path.rglob("*")) if p.is_file()}
    if not files:
        raise RuntimeError(f"empty protected tree: {path}")
    return files


def _protected_paths() -> list[Path]:
    """Return the immutable project inputs relevant to this experiment."""
    paths: set[Path] = set()
    for pattern in PROTECTED_GLOBS:
        if "*" in pattern:
            parent, glob = pattern.split("/", 1)
            paths.update((ROOT / parent).glob(glob))
        else:
            paths.add(ROOT / pattern)
    return sorted(p for p in paths if p.is_file())


def _logical(collection: Any) -> dict[str, Any]:
    """Describe copied Chroma records without modifying them."""
    data = collection.get(include=["metadatas", "embeddings"])
    vectors = [list(v) for v in data["embeddings"]]
    rows = sorted([[key, meta, vector] for key, meta, vector in zip(data["ids"], data["metadatas"], vectors)])
    return {"count": collection.count(),
            "distribution": dict(Counter(m["document_id"] for m in data["metadatas"])),
            "dimensions": sorted({len(v) for v in vectors}),
            "distance": retrieve.distance_metric(collection),
            "sha256": hashlib.sha256(json.dumps(rows, sort_keys=True, ensure_ascii=False).encode()).hexdigest()}


def _score_prefix(question: dict[str, Any], ranks: list[dict[str, Any]], k: int) -> dict[str, Any]:
    """Score source/document coverage and intrusion for a ranked prefix."""
    top = ranks[:k]
    gold = {str(ev.source_identity.DocumentSourceKey.from_dict(x)) for x in question["expected_sources"]}
    expected_docs = set(question["expected_document_ids"])
    sources = {r["document_source_key"] for r in top}
    docs = {r["document_id"] for r in top}
    return {"k": k, "source_any": bool(gold & sources), "source_all": gold <= sources,
            "document_hit": bool(expected_docs & docs), "document_all": expected_docs <= docs,
            "document_intrusion": sum(r["document_id"] not in expected_docs for r in top) / len(top),
            "retrieved_slots": len(top)}


def _rank_from_chunk(chunk: Any) -> dict[str, Any]:
    """Serialize canonical metadata and distance from a copied retrieval result."""
    return {**ev.DocumentRank.from_retrieved(chunk).to_dict(), "distance": chunk.distance}


def _metrics(question: dict[str, Any], ranks: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Compute the three requested cutoff metrics."""
    return {str(k): _score_prefix(question, ranks, k) for k in CUTOFFS}


def _normalize(vector: list[float]) -> list[float]:
    """L2-normalize one finite vector."""
    assert len(vector) == DIMENSIONS and all(math.isfinite(float(v)) for v in vector)
    norm = math.sqrt(sum(float(v) * float(v) for v in vector))
    assert norm > 0
    return [float(v) / norm for v in vector]


def _dot(a: list[float], b: list[float]) -> float:
    """Compute a cosine score for two normalized vectors."""
    return sum(x * y for x, y in zip(a, b))


def _centroids(collection: Any) -> tuple[dict[str, list[float]], dict[str, Any]]:
    """Build one normalized arithmetic centroid per document from copy embeddings."""
    data = collection.get(include=["metadatas", "embeddings"])
    grouped: dict[str, list[list[float]]] = {doc: [] for doc in DOC_IDS}
    for meta, raw in zip(data["metadatas"], data["embeddings"]):
        vector = list(raw)
        assert len(vector) == DIMENSIONS
        assert meta["document_id"] in grouped
        grouped[meta["document_id"]].append([float(v) for v in vector])
    centroids: dict[str, list[float]] = {}
    stats: dict[str, Any] = {}
    for doc, vectors in grouped.items():
        assert vectors
        mean = [sum(vector[i] for vector in vectors) / len(vectors) for i in range(DIMENSIONS)]
        mean_norm = math.sqrt(sum(v * v for v in mean))
        centroid = _normalize(mean)
        centroids[doc] = centroid
        stats[doc] = {"chunk_count": len(vectors), "dimensions": DIMENSIONS,
                      "mean_vector_l2_norm": mean_norm, "normalized_centroid_l2_norm": math.sqrt(sum(v * v for v in centroid)),
                      "centroid_sha256": hashlib.sha256(json.dumps(centroid, separators=(",", ":")).encode()).hexdigest()}
    assert {v["chunk_count"] for v in stats.values()} == {53, 276, 46}
    return centroids, stats


def _route(vector: list[float], centroids: dict[str, list[float]]) -> list[dict[str, Any]]:
    """Rank all three document centroids using the fixed cosine rule."""
    query = _normalize(vector)
    ranked = sorted((dict(document_id=doc, similarity=_dot(query, centroid)) for doc, centroid in centroids.items()),
                    key=lambda x: (-x["similarity"], x["document_id"]))
    for rank, entry in enumerate(ranked, 1):
        entry["rank"] = rank
    return ranked


def _route_docs(row: dict[str, Any], count: int) -> list[str]:
    """Return predicted document IDs without consulting gold fields."""
    return [entry["document_id"] for entry in row["routing"][:count]]


def _retrieve_copy(vector: list[float], collection: Any, documents: list[str]) -> tuple[list[dict[str, Any]], str]:
    """Retrieve Top5 from the copy using only the router-selected document set."""
    where: dict[str, Any]
    if len(documents) == 1:
        where = {"document_id": documents[0]}
        chunks = retrieve.retrieve_by_embedding(vector, collection=collection, top_k=5, where=where)
        return [_rank_from_chunk(c) for c in chunks], "where_document_id_eq"
    where = {"document_id": {"$in": documents}}
    try:
        chunks = retrieve.retrieve_by_embedding(vector, collection=collection, top_k=5, where=where)
        return [_rank_from_chunk(c) for c in chunks], "where_document_id_in"
    except Exception:
        # Experiment-only copy fallback for Chroma versions without `$in`.
        data = collection.get(where=where, include=["documents", "metadatas", "embeddings"])
        candidates = []
        for chunk_id, text, meta, embedding in zip(data["ids"], data["documents"], data["metadatas"], data["embeddings"]):
            distance = sum((float(a) - float(b)) ** 2 for a, b in zip(vector, embedding))
            candidates.append((distance, chunk_id, text, meta))
        candidates.sort(key=lambda x: (x[0], x[1]))
        rows = []
        for rank, (distance, chunk_id, text, meta) in enumerate(candidates[:5], 1):
            fake = retrieve.RetrievedChunk(rank=rank, chunk_id=chunk_id, text=text, metadata=meta, distance=distance)
            rows.append(_rank_from_chunk(fake))
        return rows, "copy_get_l2_fallback"


def _b0_rows(questions: list[ev.DocumentQuestion]) -> dict[str, dict[str, Any]]:
    """Load the saved M12F-B raw/global result without rerunning it."""
    saved = json.loads(B0_PATH.read_bytes())
    rows = {r["question"]["id"]: r for r in saved["results"]}
    assert len(rows) == 105
    assert all(rows[q.id]["question"] == q.to_dict() for q in questions)
    return rows


def _input_state(questions: list[ev.DocumentQuestion]) -> dict[str, Any]:
    """Create the immutable input fingerprint set."""
    paths = _protected_paths()
    return {p.relative_to(ROOT).as_posix(): _hash(p) for p in paths}


def prepare() -> None:
    """Verify clean preconditions and create a byte-identical Chroma copy."""
    if OUT.with_suffix(".json").exists():
        raise RuntimeError("Existing M12F-D report; refusing replacement")
    questions = population()
    git = lambda *args: subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    assert git("rev-parse", "HEAD") == HEAD
    assert git("rev-parse", "origin/main") == HEAD
    status_lines = [line for line in git("status", "--short").splitlines() if line]
    allowed_status = {
        "scripts/run_m12fd_centroid_routing.py", "tests/test_m12fd_centroid_routing.py",
        "reports/evaluation/m12fd-centroid-routing.json", "reports/evaluation/m12fd-centroid-routing.csv",
        "reports/evaluation/m12fd-centroid-routing.md",
    }
    assert all(line[3:] in allowed_status for line in status_lines)
    production = (ROOT / config.CHROMA_PATH).resolve()
    before = _tree(production)
    copy = Path(tempfile.mkdtemp(prefix="m12fd-chroma-copy-")) / "chroma"
    assert production != copy.resolve() and production not in copy.resolve().parents
    shutil.copytree(production, copy)
    copied = _tree(copy)
    assert before == copied == _tree(production)
    collection = m12d.chromadb.PersistentClient(path=str(copy)).get_collection(config.COLLECTION_NAME, embedding_function=None)
    logical = _logical(collection)
    assert logical["count"] == 375 and logical["distribution"] == m12d.DISTRIBUTION
    assert logical["dimensions"] == [DIMENSIONS] and logical["distance"] == "l2"
    assert config.EMBEDDING_MODEL == MODEL
    explicit = [q for q in questions if len(detect_laws(q.question)) == 1]
    assert len(explicit) == 6
    state = {
        "status": "prepared", "verdict": "M12F-D BLOCKED — EXPERIMENT ISSUE", "head": HEAD,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "population": {"count": 105, "composition": {"5326": 45, "4458": 30, "5607": 30},
                        "implicit": 99, "explicit": 6, "full_records_identical": True,
                        "loader": "scripts.run_m12d_three_source._questions"},
        "detector_reporting_only": {"implicit": [q.id for q in questions if len(detect_laws(q.question)) != 1],
                                     "explicit": [q.id for q in explicit],
                                     "detector_used_for_routing": False},
        "configuration": {"model": MODEL, "dimensions": DIMENSIONS, "router": "normalized query dot normalized arithmetic document centroid",
                           "query": "raw original question exactly", "top_k": 5, "max_retries": 0,
                           "title_enrichment": False, "rerank": False, "deduplicate": False,
                           "supervised_fitting": False, "hybrid": False},
        "chroma": {"production_path": str(production), "copy_path": str(copy), "production_files_before": before,
                   "copy_files_before_open": copied, "byte_equal_before_open": True, "logical_before": logical},
        "input_hashes": _input_state(questions),
        "api": {"unique_embedding_inputs": 0, "requests": 0, "successful_embeddings": 0, "failures": 0,
                "prompt_tokens": 0, "total_tokens": 0, "generation_calls": 0},
        "copy_query_operations": {"R1": 0, "R2": 0}, "results": [], "centroid_statistics": {},
    }
    _save(state)
    print("Prepared: 105 questions; implicit=99; explicit=6; copy 375 records; no API calls.", flush=True)


def run() -> None:
    """Run exactly one raw-query embedding batch and two copy-only routes."""
    state = _load()
    if state["status"] == "blocked" and state.get("error_type") == "APIConnectionError" and not state.get("results"):
        state["network_recovery"] = {"initial_attempt": "sandbox APIConnectionError", "recovered_with_escalated_execution": True}
        state["status"] = "prepared"
        state["api"] = {"unique_embedding_inputs": 0, "requests": 0, "successful_embeddings": 0, "failures": 0,
                         "prompt_tokens": 0, "total_tokens": 0, "generation_calls": 0}
        state["copy_query_operations"] = {"R1": 0, "R2": 0}
        state["results"] = []
    assert state["status"] == "prepared", "Already attempted; do not rerun"
    questions = population()
    assert _input_state(questions) == state["input_hashes"]
    production = Path(state["chroma"]["production_path"]).resolve()
    copy = Path(state["chroma"]["copy_path"]).resolve()
    assert production != copy and production not in copy.parents
    assert _tree(production) == state["chroma"]["production_files_before"]
    collection = m12d.chromadb.PersistentClient(path=str(copy)).get_collection(config.COLLECTION_NAME, embedding_function=None)
    assert _logical(collection) == state["chroma"]["logical_before"]
    state["status"] = "running"
    _save(state)
    try:
        centroids, centroid_stats = _centroids(collection)
        state["centroid_statistics"] = centroid_stats
        pairs = [(MODEL, q.question) for q in questions]
        with OpenAI(api_key=config.OPENAI_API_KEY, max_retries=0, timeout=60.0) as client:
            vectors = cached_embeddings(client.embeddings, pairs, state["api"])
        assert len(vectors) == 105
        b0 = _b0_rows(questions)
        for q in questions:
            vector = vectors[(MODEL, q.question)]
            routing = _route(vector, centroids)
            expected_docs = sorted(q.expected_document_ids)
            row = {"question": q.to_dict(), "routing": routing, "true_document_ids": expected_docs,
                   "query_input_sha256": hashlib.sha256(q.question.encode("utf-8")).hexdigest(), "variants": {}}
            b0_result = b0[q.id]
            row["variants"]["B0"] = {"ranks": b0_result["ranks"], "metrics": b0_result["metrics"], "source": "saved M12F-B raw/global"}
            for variant, count in (("R1", 1), ("R2", 2)):
                ranks, filter_mode = _retrieve_copy(vector, collection, _route_docs(row, count))
                assert len(ranks) == 5 and len({r["chunk_id"] for r in ranks}) == 5
                row["variants"][variant] = {"ranks": ranks, "metrics": _metrics(q.to_dict(), ranks), "filter_mode": filter_mode,
                                              "route_documents": _route_docs(row, count)}
                state["copy_query_operations"][variant] += 1
            state["results"].append(row)
            if len(state["results"]) % 15 == 0:
                _save(state)
                print(f"Saved {len(state['results'])}/105 routed results", flush=True)
        assert len(state["results"]) == 105
        state["status"] = "completed"
    except Exception as exc:
        state["status"] = "blocked"
        state["error_type"] = type(exc).__name__
        state["error_message"] = str(exc)
        print("STOP: " + type(exc).__name__, flush=True)
    finally:
        state["chroma"]["production_files_after"] = _tree(production)
        state["chroma"]["production_unchanged"] = state["chroma"]["production_files_after"] == state["chroma"]["production_files_before"]
        state["chroma"]["logical_after"] = _logical(collection)
        state["chroma"]["logical_unchanged"] = state["chroma"]["logical_after"] == state["chroma"]["logical_before"]
        state["inputs_unchanged"] = _input_state(questions) == state["input_hashes"]
        if not all((state["chroma"]["production_unchanged"], state["chroma"]["logical_unchanged"], state["inputs_unchanged"])):
            state["status"] = "blocked"
        if state["status"] == "completed":
            _save(state)
            render()
        else:
            _save(state)
    if state["status"] != "completed":
        raise SystemExit(1)


def _group_rows(state: dict[str, Any], questions: list[ev.DocumentQuestion], label: str) -> list[dict[str, Any]]:
    """Select rows for a reporting subgroup."""
    ids = {q.id for q in questions if label == "all" or
           (label == "implicit" and len(detect_laws(q.question)) != 1) or
           (label == "explicit" and len(detect_laws(q.question)) == 1) or
           (label == "single_source" and len(q.expected_sources) == 1) or
           (label == "multi_source" and len(q.expected_sources) > 1) or
           (label == "doc_5326" and m12d.DOCS["5326"] in q.expected_document_ids) or
           (label == "doc_4458" and m12d.DOCS["4458"] in q.expected_document_ids) or
           (label == "doc_5607" and m12d.DOCS["5607"] in q.expected_document_ids)}
    return [r for r in state["results"] if r["question"]["id"] in ids]


def _summary(rows: list[dict[str, Any]], variant: str) -> dict[str, Any]:
    """Aggregate metrics as exact fractions and metric means."""
    return {str(k): {metric: sum(bool(r["variants"][variant]["metrics"][str(k)][metric]) for r in rows) / len(rows)
                     for metric in ("source_any", "source_all", "document_hit", "document_all")}
            | {"document_intrusion": sum(r["variants"][variant]["metrics"][str(k)]["document_intrusion"] for r in rows) / len(rows)}
            for k in CUTOFFS}


def _paired(rows: list[dict[str, Any]], variant: str, cutoff: str, metric: str) -> dict[str, Any]:
    """Return exact IDs whose boolean coverage changed against saved B0."""
    groups = {name: [] for name in ("improved", "unchanged", "regressed")}
    for row in rows:
        old = bool(row["variants"]["B0"]["metrics"][cutoff][metric])
        new = bool(row["variants"][variant]["metrics"][cutoff][metric])
        groups["improved" if new and not old else "regressed" if old and not new else "unchanged"].append(row["question"]["id"])
    return {key: {"count": len(value), "ids": value} for key, value in groups.items()}


def _route_accuracy(rows: list[dict[str, Any]], questions: list[ev.DocumentQuestion]) -> dict[str, Any]:
    """Compute Top1/Top2 routing accuracy by true document and subgroup."""
    result = {}
    for label in ("all", "implicit", "explicit"):
        ids = {q.id for q in questions if label == "all" or
               (label == "implicit" and len(detect_laws(q.question)) != 1) or
               (label == "explicit" and len(detect_laws(q.question)) == 1)}
        group = [r for r in rows if r["question"]["id"] in ids]
        result[label] = {"count": len(group), "top1": sum(bool(set(r["true_document_ids"]) & {r["routing"][0]["document_id"]}) for r in group),
                         "top2": sum(bool(set(r["true_document_ids"]) & {x["document_id"] for x in r["routing"][:2]}) for r in group)}
        result[label]["top1_accuracy"] = result[label]["top1"] / len(group)
        result[label]["top2_accuracy"] = result[label]["top2"] / len(group)
        result[label]["by_true_document"] = {}
        for doc in DOC_IDS:
            subset = [r for r in group if doc in r["true_document_ids"]]
            result[label]["by_true_document"][doc] = {"count": len(subset),
                "top1": sum(r["routing"][0]["document_id"] == doc for r in subset),
                "top2": sum(doc in {x["document_id"] for x in r["routing"][:2]} for r in subset)}
    confusion = {true: {pred: 0 for pred in DOC_IDS} for true in DOC_IDS}
    for r in rows:
        for true in r["true_document_ids"]:
            confusion[true][r["routing"][0]["document_id"]] += 1
    result["confusion_matrix"] = confusion
    result["error_ids"] = [r["question"]["id"] for r in rows if r["routing"][0]["document_id"] not in r["true_document_ids"]]
    return result


def _margin_summary(rows: list[dict[str, Any]], correct: bool) -> dict[str, Any]:
    """Summarize Top1-minus-Top2 centroid margins."""
    values = [r["routing"][0]["similarity"] - r["routing"][1]["similarity"] for r in rows if (r["routing"][0]["document_id"] in r["true_document_ids"]) == correct]
    return {"count": len(values), "mean": statistics.mean(values) if values else None,
            "median": statistics.median(values) if values else None, "min": min(values) if values else None, "max": max(values) if values else None}


def _router_errors(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Describe the retrieval cost of each Top1 routing error."""
    errors = []
    for row in rows:
        route = row["routing"]
        if route[0]["document_id"] in row["true_document_ids"]:
            continue
        b0 = row["variants"]["B0"]["metrics"]["5"]
        r1 = row["variants"]["R1"]["metrics"]["5"]
        r2 = row["variants"]["R2"]["metrics"]["5"]
        labels = []
        if (b0["source_any"] and not r1["source_any"]) or (b0["source_all"] and not r1["source_all"]): labels.append("A R1 catastrophic regression")
        if (not r1["source_any"] and r2["source_any"]) or (not r1["source_all"] and r2["source_all"]): labels.append("B R2 recovers the error")
        if not b0["source_any"] and not b0["source_all"]: labels.append("C B0 was already wrong")
        if b0["source_any"] == r1["source_any"] and b0["source_all"] == r1["source_all"]: labels.append("D no retrieval impact")
        errors.append({"id": row["question"]["id"], "true_document": row["true_document_ids"], "predicted_document": route[0]["document_id"],
                       "second_document": route[1]["document_id"], "similarity_gap": route[0]["similarity"] - route[1]["similarity"],
                       "B0_source_any_5": b0["source_any"], "B0_source_all_5": b0["source_all"],
                       "R1_source_any_5": r1["source_any"], "R1_source_all_5": r1["source_all"],
                       "R2_source_any_5": r2["source_any"], "R2_source_all_5": r2["source_all"], "classification": labels})
    return errors


def render() -> None:
    """Derive evaluation and reports from saved JSON without Chroma or API access."""
    state = _load()
    assert state["status"] == "completed" and len(state["results"]) == 105
    questions = population()
    rows = state["results"]
    state["routing_accuracy"] = _route_accuracy(rows, questions)
    state["routing_errors"] = _router_errors(rows)
    margins = {"correct_top1": _margin_summary(rows, True), "incorrect_top1": _margin_summary(rows, False)}
    margins["interpretation"] = ("Incorrect Top1 routes have lower mean and median margins than correct routes "
                                  f"({margins['incorrect_top1']['mean']:.6f}/{margins['incorrect_top1']['median']:.6f} "
                                  f"versus {margins['correct_top1']['mean']:.6f}/{margins['correct_top1']['median']:.6f}); "
                                  "the distributions overlap and no production threshold is selected.")
    state["margin_analysis"] = margins
    labels = ("all", "implicit", "explicit", "single_source", "multi_source", "doc_5326", "doc_4458", "doc_5607")
    state["summaries"] = {v: {label: _summary(_group_rows(state, questions, label), v) for label in labels} for v in VARIANTS}
    state["paired_changes"] = {v: {metric: {str(k): _paired(rows, v, str(k), metric) for k in (1, 3, 5)}
                                      for metric in ("source_any", "source_all", "document_hit")} for v in ("R1", "R2")}
    state["primary_cases"] = {}
    for qid in PRIMARY + DRIFT + CONTROLS:
        row = next(r for r in rows if r["question"]["id"] == qid)
        expected = {str(ev.source_identity.DocumentSourceKey.from_dict(x)) for x in row["question"]["expected_sources"]}
        state["primary_cases"][qid] = {"routing": row["routing"], "true_document_rank": next((x["rank"] for x in row["routing"] if x["document_id"] in row["true_document_ids"]), None),
            "variants": {v: {"top5_chunk_ids": [x["chunk_id"] for x in row["variants"][v]["ranks"][:5]],
                             "expected_source_ranks": {key: next((x["rank"] for x in row["variants"][v]["ranks"] if x["document_source_key"] == key), None) for key in sorted(expected)},
                             "metrics": row["variants"][v]["metrics"]} for v in VARIANTS}}
    state["comparison_caveat"] = "B0 is saved historical M12F-B raw/global evidence; R1/R2 are fresh routed retrieval from one new query-embedding batch, so this is development evidence rather than a perfectly same-run causal comparison."
    state["verdict"] = "M12F-D READY FOR REVIEW — ROUTER NOT SUFFICIENT"
    state["review_conclusion"] = "The fixed unsupervised centroid router is diagnostic only. No benchmark-label fitting, production change, candidate adoption or routing implementation occurred."
    state["next_experiment"] = "Run one development-only LLM-based question-only document-router comparison, without gold document input; continue separate multi-source provision coverage tracking. A NEW UNSEEN HOLDOUT is required before adoption."
    _save(state)
    _render_files(state, questions)
    print(json.dumps({"verdict": state["verdict"], "api": state["api"], "copy_queries": state["copy_query_operations"],
                      "routing": state["routing_accuracy"]["all"], "errors": len(state["routing_errors"])}, ensure_ascii=False), flush=True)


def _render_files(state: dict[str, Any], questions: list[ev.DocumentQuestion]) -> None:
    """Render CSV and reviewable Markdown from saved state."""
    rows = state["results"]
    fields = ["id", "question", "variant", "rank", "chunk_id", "document_source_key", "document_id", "distance", "expected_sources"]
    with OUT.with_suffix(".csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            expected = " | ".join(sorted(str(ev.source_identity.DocumentSourceKey.from_dict(x)) for x in row["question"]["expected_sources"]))
            for variant in VARIANTS:
                for rank in row["variants"][variant]["ranks"]:
                    writer.writerow({"id": row["question"]["id"], "question": row["question"]["question"], "variant": variant,
                                     "expected_sources": expected, **{k: rank.get(k) for k in fields if k in rank}})
    lines = ["# M12F-D — Implicit Document Centroid Routing Experiment", "", state["verdict"], "",
             "Development-only diagnostic. No production retrieval, Chroma, chunking, corpus embedding, LLM router, title enrichment, BM25/RRF, supervised fitting or adoption.",
             "A NEW UNSEEN HOLDOUT is mandatory before any future production adoption.", "",
             "## Population and immutable scope", "", "105 exact M12D questions: 5326=45, 4458=30, 5607=30; implicit=99, explicit=6. The M12F-A literal-law detector is used only for reporting subgroups and never for routing.",
             "Centroids use all existing copy embeddings: 5326=53, 4458=276, 5607=46; 1536 dimensions; one arithmetic mean per document followed by L2 normalization. No document is weighted by chunk count.",
             state["comparison_caveat"], "", "## Accounting", "", "```json", json.dumps({"api": state["api"], "copy_query_operations": state["copy_query_operations"], "centroid_statistics": state["centroid_statistics"]}, ensure_ascii=False, indent=2), "```", "",
             f"Production Chroma unchanged: {state['chroma']['production_unchanged']}; copy logical state unchanged: {state['chroma']['logical_unchanged']}; protected inputs unchanged: {state['inputs_unchanged']}.", "",
             "## Router-only accuracy", "", "| Group | N | Top1 | Top2 |", "|---|---:|---:|---:|"]
    for label in ("all", "implicit", "explicit"):
        a = state["routing_accuracy"][label]
        lines.append(f"| {label} | {a['count']} | {a['top1']} ({a['top1_accuracy']:.2%}) | {a['top2']} ({a['top2_accuracy']:.2%}) |")
    lines += ["", "### Per-document accuracy", "", "| Group | True document | N | Top1 | Top2 |", "|---|---|---:|---:|---:|"]
    for label in ("all", "implicit", "explicit"):
        for doc, a in state["routing_accuracy"][label]["by_true_document"].items():
            lines.append(f"| {label} | {doc} | {a['count']} | {a['top1']} | {a['top2']} |")
    lines += ["", "### Top1 confusion matrix", "", "| True \\ Predicted | " + " | ".join(DOC_IDS) + " |", "|---|" + "---:|" * len(DOC_IDS)]
    for true, values in state["routing_accuracy"]["confusion_matrix"].items():
        lines.append("| " + true + " | " + " | ".join(str(values[p]) for p in DOC_IDS) + " |")
    lines += ["", "Top1 routing errors: " + (", ".join(state["routing_accuracy"]["error_ids"]) or "none") + ".", "", "## Margin analysis", "", "```json", json.dumps(state["margin_analysis"], ensure_ascii=False, indent=2), "```", "", "## B0 / R1 / R2 metrics", "", "Coverage cells are fractions; document intrusion is the mean fraction of returned slots whose document is outside the gold document set.", ""]
    for label in ("all", "doc_5326", "doc_4458", "doc_5607", "implicit", "explicit", "single_source", "multi_source"):
        lines += [f"### {label}", "", "| Variant | Metric | @1 | @3 | @5 |", "|---|---|---:|---:|---:|"]
        for v in VARIANTS:
            for metric in ("source_any", "source_all", "document_hit", "document_all", "document_intrusion"):
                vals = state["summaries"][v][label]
                lines.append(f"| {v} | {metric} | " + " | ".join(f"{vals[str(k)][metric]:.2%}" for k in CUTOFFS) + " |")
    lines += ["", "## Paired changes against saved B0 at @5", "", "| Candidate | Metric | Improved | Unchanged | Regressed |", "|---|---|---:|---:|---:|"]
    for v in ("R1", "R2"):
        for metric in ("source_any", "source_all", "document_hit"):
            x = state["paired_changes"][v][metric]["5"]
            lines.append(f"| {v} | {metric} | {x['improved']['count']} | {x['unchanged']['count']} | {x['regressed']['count']} |")
            lines.append(f"| {v} | {metric} improvement IDs | {', '.join(x['improved']['ids']) or '—'} | | |")
            lines.append(f"| {v} | {metric} regression IDs | | | {', '.join(x['regressed']['ids']) or '—'} |")
    lines += ["", "## Router error cost", "", "```json", json.dumps(state["routing_errors"], ensure_ascii=False, indent=2), "```", "", "## Primary and control cases", ""]
    for qid, case in state["primary_cases"].items():
        lines += [f"### {qid}", "", "Routing: " + "; ".join(f"{x['rank']} {x['document_id']}={x['similarity']:.9f}" for x in case["routing"]), f"True document rank: {case['true_document_rank']}", ""]
        for v in VARIANTS:
            lines.append(f"- {v} Top5: {', '.join(case['variants'][v]['top5_chunk_ids'])}; expected source ranks: " + ", ".join(f"{k}={r if r is not None else 'MISS'}" for k, r in case["variants"][v]["expected_source_ranks"].items()))
        lines.append("")
    lines += ["## Interpretation", "", "003/004 are evaluated as document-discrimination cases when the router predicts 5607 and retrieval improves; 026/029 remain separate within-document provision-selection tests if either expected source remains outside Top5. 025 remains a multi-source composite test.", "", state["review_conclusion"], "", "Next experiment: " + state["next_experiment"], "", "No candidate is adopted. No commit is part of this milestone."]
    OUT.with_suffix(".md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    """Keep preparation, one real run and offline rendering separate."""
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("prepare", "run", "render"))
    args = parser.parse_args()
    {"prepare": prepare, "run": run, "render": render}[args.phase]()


if __name__ == "__main__":
    main()
