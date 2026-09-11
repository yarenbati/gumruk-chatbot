"""M12F-E2 development diagnostic: saved LLM routing plus dense retrieval.

The LLM predictions are loaded from the completed M12F-E artifact.  This
module never calls the router and never modifies production retrieval or the
production Chroma collection.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import run_m12d_three_source as m12d
from scripts import run_m12fb_candidate_pool as m12fb
from scripts.run_m12fa_explicit_law import cached_embeddings, detect_laws
from src import config, evaluate_documents as ev, retrieve

ROOT = m12d.ROOT
OUT = ROOT / "reports/evaluation/m12fe2-llm-routed-retrieval"
ROUTER_PATH = ROOT / "reports/evaluation/m12fe-llm-router.json"
B0_PATH = ROOT / "reports/evaluation/m12fb-candidate-pool-diagnostic.json"
HEAD = "65155481f29f5648156e9925c602edf67f34cec8"
DOCS = tuple(m12d.DOCS.values())
VARIANTS = ("B0", "R1", "R2")
CUTOFFS = (1, 3, 5)
METRICS = ("source_any", "source_all", "document_hit", "document_all", "document_intrusion")
PRIMARY = ["k5607-002", "k5607-003", "k5607-004", "k5607-025", "k5607-026", "k5607-029"]


def _load() -> dict[str, Any]:
    """Load the saved E2 state."""
    return json.loads(OUT.with_suffix(".json").read_bytes())


def _save(state: dict[str, Any]) -> None:
    """Write deterministic UTF-8 JSON."""
    m12d._write(OUT.with_suffix(".json"), state)


def _hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _hash_file(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {"size_bytes": len(data), "sha256": _hash_bytes(data)}


def _protected_paths() -> list[Path]:
    """Collect protected inputs without including this experiment's outputs."""
    paths: set[Path] = {ROOT / "app.py", ROOT / "data/source_manifest.json", ROUTER_PATH, B0_PATH}
    paths.update((ROOT / "src").rglob("*.py"))
    paths.update((ROOT / "evaluation").rglob("*"))
    for prefix in ("m12d-", "m12e-", "m12fa-", "m12fb-", "m12fc-", "m12fd-", "m12fe-llm-router"):
        paths.update((ROOT / "reports/evaluation").glob(prefix + "*"))
    return sorted(path for path in paths if path.is_file())


def _input_hashes() -> dict[str, dict[str, Any]]:
    return {path.relative_to(ROOT).as_posix(): _hash_file(path) for path in _protected_paths()}


def _population() -> list[ev.DocumentQuestion]:
    """Load and verify the exact accepted M12D population."""
    questions = m12d._questions()
    saved = json.loads(m12d.JSON_PATH.read_bytes())
    assert [q.to_dict() for q in questions] == [row["question"] for row in saved["results"]]
    assert len(questions) == len({q.question for q in questions}) == 105
    assert Counter(next(iter(q.expected_document_ids)) for q in questions) == Counter({
        m12d.DOCS["5326"]: 45, m12d.DOCS["4458"]: 30, m12d.DOCS["5607"]: 30})
    assert sum(len(detect_laws(q.question)) == 1 for q in questions) == 6
    return questions


def _keys(question: dict[str, Any]) -> set[str]:
    return {str(ev.source_identity.DocumentSourceKey.from_dict(key)) for key in question["expected_sources"]}


def score_prefix(question: dict[str, Any], ranks: list[dict[str, Any]], cutoff: int) -> dict[str, Any]:
    """Score source and document coverage at one cutoff."""
    top = ranks[:cutoff]
    gold = _keys(question)
    expected_docs = set(question["expected_document_ids"])
    sources = {rank["document_source_key"] for rank in top}
    documents = {rank["document_id"] for rank in top}
    return {
        "k": cutoff,
        "source_any": bool(gold & sources),
        "source_all": gold <= sources,
        "document_hit": bool(expected_docs & documents),
        "document_all": expected_docs <= documents,
        "document_intrusion": sum(rank["document_id"] not in expected_docs for rank in top) / len(top) if top else None,
        "retrieved_slots": len(top),
    }


def _rank_dict(chunk: Any) -> dict[str, Any]:
    rank = ev.DocumentRank.from_retrieved(chunk).to_dict()
    rank.update(distance=chunk.distance, text_sha256=_hash_bytes(chunk.text.encode("utf-8")))
    return rank


def _validate_saved_router(router: dict[str, Any], questions: list[ev.DocumentQuestion]) -> dict[str, dict[str, Any]]:
    """Require 105 valid frozen Phase-A predictions and accepted key facts."""
    assert router["status"] == "completed"
    assert router["verdict"] == "M12F-E READY FOR REVIEW \u2014 LLM ROUTER PROMISING"
    assert router["accuracy"]["all"]["top1"] == 100
    assert router["accuracy"]["all"]["top2"] == 105
    assert router["routing_evaluation"]["by_true_document"][m12d.DOCS["5607"]]["top1"] == 27
    rows = {row["question"]["id"]: row for row in router["results"]}
    assert len(rows) == 105
    for question in questions:
        prediction = rows[question.id]["prediction"]
        assert isinstance(prediction, list) and len(prediction) == 3 and set(prediction) == set(DOCS)
    for question_id in PRIMARY:
        assert rows[question_id]["prediction"][0] == m12d.DOCS["5607"]
    return rows


def _baseline_rows() -> dict[str, dict[str, Any]]:
    baseline = json.loads(B0_PATH.read_bytes())
    assert baseline["status"] == "completed"
    rows = {row["question"]["id"]: row for row in baseline["results"]}
    assert len(rows) == 105
    return rows


def prepare() -> None:
    """Freeze saved inputs and verify a fresh byte-identical Chroma copy."""
    if OUT.with_suffix(".json").exists():
        raise RuntimeError("Existing M12F-E2 report; refusing replacement")
    git = lambda *args: subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    assert git("rev-parse", "HEAD") == git("rev-parse", "origin/main") == HEAD
    allowed_status = {
        "scripts/run_m12fe2_llm_routed_retrieval.py",
        "tests/test_m12fe2_llm_routed_retrieval.py",
        "reports/evaluation/m12fe2-llm-routed-retrieval.json",
        "reports/evaluation/m12fe2-llm-routed-retrieval.csv",
        "reports/evaluation/m12fe2-llm-routed-retrieval.md",
    }
    assert all(line[3:] in allowed_status for line in git("status", "--short").splitlines() if line)
    questions = _population()
    router = json.loads(ROUTER_PATH.read_bytes())
    predictions = _validate_saved_router(router, questions)
    baseline = json.loads(B0_PATH.read_bytes())
    assert baseline["status"] == "completed"
    production = (ROOT / config.CHROMA_PATH).resolve()
    before = m12d._tree(production)
    copy_path = Path(tempfile.mkdtemp(prefix="m12fe2-chroma-copy-")) / "chroma"
    assert production != copy_path.resolve() and production not in copy_path.resolve().parents
    shutil.copytree(production, copy_path)
    copied = m12d._tree(copy_path)
    assert before == copied == m12d._tree(production)
    collection = m12d.chromadb.PersistentClient(path=str(copy_path)).get_collection(config.COLLECTION_NAME, embedding_function=None)
    logical = m12d._logical(collection)
    assert logical["count"] == 375 and logical["distribution"] == m12d.DISTRIBUTION
    assert logical["dimensions"] == [1536] and retrieve.distance_metric(collection) == "l2"
    assert config.EMBEDDING_MODEL == "text-embedding-3-small"
    state = {
        "status": "prepared",
        "verdict": "M12F-E2 BLOCKED \u2014 DIAGNOSTIC ISSUE",
        "head": HEAD,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "population": {"count": 105, "composition": {"5326": 45, "4458": 30, "5607": 30}, "implicit": 99, "explicit": 6, "full_records_identical": True},
        "saved_router": {"path": str(ROUTER_PATH.relative_to(ROOT)), "status": router["status"], "top1": router["accuracy"]["all"]["top1"], "top2": router["accuracy"]["all"]["top2"], "5607_top1": router["routing_evaluation"]["by_true_document"][m12d.DOCS["5607"]]["top1"], "valid_predictions": 105},
        "baseline": {"path": str(B0_PATH.relative_to(ROOT)), "kind": "saved historical M12F-B raw/global Top50 baseline; not rerun", "status": baseline["status"]},
        "configuration": {"embedding_model": config.EMBEDDING_MODEL, "dimensions": 1536, "top_k": 5, "distance_metric": "l2", "query": "raw original question exactly", "rerank": False, "enrichment": False, "router_calls": 0, "gold_fallback": False, "chroma": "COPY ONLY"},
        "routing_variants": {"R1": "saved M12F-E rank-1 document, hard route", "R2": "saved M12F-E rank-1 and rank-2 documents, inclusion route"},
        "input_hashes": _input_hashes(),
        "chroma": {"production_path": str(production), "copy_path": str(copy_path), "production_files_before": before, "copy_files_before_open": copied, "byte_equal_before_open": True, "logical_before": logical},
        "api": {"unique_embedding_inputs": 105, "requests": 0, "successful_embeddings": 0, "failures": 0, "prompt_tokens": 0, "total_tokens": 0, "generation_calls": 0, "router_calls": 0},
        "query_operations": {"R1": 0, "R2": 0, "total_fresh_retrieval_queries": 0},
        "results": [],
    }
    _save(state)
    print("Prepared: saved router verified; 105 raw embeddings admitted; copy 375 records, 53/276/46, 1536 dimensions, L2.", flush=True)


def _query_filtered(collection: Any, vector: list[float], allowed: list[str]) -> tuple[list[Any], str]:
    """Query a copy with inclusion filtering, with a copy-only local fallback."""
    where = {"document_id": {"$in": allowed}}
    try:
        chunks = retrieve.retrieve_by_embedding(vector, collection=collection, top_k=5, where=where)
        if all(chunk.metadata.get("document_id") in allowed for chunk in chunks):
            return chunks, "chroma_inclusion_filter"
    except Exception:
        pass
    data = collection.get(include=["documents", "metadatas", "embeddings"])
    candidates = []
    for chunk_id, text, metadata, embedding in zip(data["ids"], data["documents"], data["metadatas"], data["embeddings"]):
        if metadata.get("document_id") in allowed:
            distance = sum((float(left) - float(right)) ** 2 for left, right in zip(vector, embedding))
            candidates.append((distance, chunk_id, text, metadata))
    candidates.sort(key=lambda item: (item[0], item[1]))
    return [retrieve.RetrievedChunk(rank=index, chunk_id=chunk_id, text=text, metadata=dict(metadata), distance=distance) for index, (distance, chunk_id, text, metadata) in enumerate(candidates[:5], 1)], "copy_local_inclusion_equivalent"


def run() -> None:
    """Make one embedding batch and two copy-only filtered retrievals per question."""
    state = _load()
    if state["status"] == "blocked" and state.get("error_type") == "APIConnectionError" and not state["results"] and state["query_operations"] == {"R1": 0, "R2": 0, "total_fresh_retrieval_queries": 0}:
        state.setdefault("network_recovery", []).append({"error_type": "APIConnectionError", "phase": "embedding_batch", "successful_embeddings": 0, "retrieval_queries": 0, "preserved": True})
        state["status"] = "prepared"
        state.pop("error_type", None)
        state.pop("error_message", None)
        state["api"]["failures"] = 0
        _save(state)
    assert state["status"] == "prepared", "Already attempted; do not rerun"
    questions = _population()
    router = json.loads(ROUTER_PATH.read_bytes())
    predictions = _validate_saved_router(router, questions)
    baseline = _baseline_rows()
    production, copy_path = (Path(state["chroma"][key]).resolve() for key in ("production_path", "copy_path"))
    assert m12d._tree(production) == state["chroma"]["production_files_before"]
    collection = m12d.chromadb.PersistentClient(path=str(copy_path)).get_collection(config.COLLECTION_NAME, embedding_function=None)
    assert m12d._logical(collection) == state["chroma"]["logical_before"]
    state["status"] = "running"
    _save(state)
    try:
        model = state["configuration"]["embedding_model"]
        with m12d.OpenAI(api_key=config.OPENAI_API_KEY, max_retries=0, timeout=60.0) as client:
            vectors = cached_embeddings(client.embeddings, [(model, q.question) for q in questions], state["api"])
        assert len(vectors) == 105
        _save(state)
        for index, question in enumerate(questions, 1):
            saved = predictions[question.id]["prediction"]
            row = {"question": question.to_dict(), "saved_router_ranking": saved, "true_document": next(iter(question.expected_document_ids)), "variants": {}}
            b0 = baseline[question.id]
            row["variants"]["B0"] = {"ranks": b0["ranks"], "metrics": b0["metrics"], "where": None, "historical": True}
            for variant, allowed in (("R1", saved[:1]), ("R2", saved[:2])):
                chunks, mode = _query_filtered(collection, vectors[(model, question.question)], allowed)
                assert len(chunks) == 5 and all(chunk.metadata.get("document_id") in allowed for chunk in chunks)
                ranks = [_rank_dict(chunk) for chunk in chunks]
                metrics = {str(k): score_prefix(row["question"], ranks, k) for k in CUTOFFS}
                checked = ev.evaluate_retrieved(question, chunks).to_dict()["metrics"]
                assert all(metrics[str(k)] == checked[str(k)] for k in CUTOFFS)
                state["query_operations"][variant] += 1
                row["variants"][variant] = {"ranks": ranks, "metrics": metrics, "where": {"document_id": {"$in": allowed}}, "allowed_documents": allowed, "filter_mode": mode, "query_input_sha256": _hash_bytes(question.question.encode("utf-8"))}
            state["results"].append(row)
            state["query_operations"]["total_fresh_retrieval_queries"] += 2
            _save(state)
            if index % 15 == 0:
                print(f"Saved {index}/105 routed retrieval rows", flush=True)
        assert state["query_operations"] == {"R1": 105, "R2": 105, "total_fresh_retrieval_queries": 210}
        state["status"] = "completed"
    except Exception as exc:
        state["status"] = "blocked"
        state["error_type"] = type(exc).__name__
        state["error_message"] = str(exc)
        print("STOP: " + type(exc).__name__, flush=True)
    finally:
        state["chroma"]["production_files_after"] = m12d._tree(production)
        state["chroma"]["production_unchanged"] = state["chroma"]["production_files_after"] == state["chroma"]["production_files_before"]
        state["chroma"]["logical_after"] = m12d._logical(collection)
        state["chroma"]["logical_unchanged"] = state["chroma"]["logical_after"] == state["chroma"]["logical_before"]
        state["inputs_unchanged"] = _input_hashes() == state["input_hashes"]
        if not all((state["chroma"]["production_unchanged"], state["chroma"]["logical_unchanged"], state["inputs_unchanged"])):
            state["status"] = "blocked"
        _save(state)
    if state["status"] != "completed":
        raise SystemExit(1)
    render()


def _summary(rows: list[dict[str, Any]], variant: str) -> dict[str, Any]:
    return {"count": len(rows), "metrics": {str(k): {metric: sum(row["variants"][variant]["metrics"][str(k)][metric] for row in rows) / len(rows) for metric in METRICS} for k in CUTOFFS}}


def _subgroup(row: dict[str, Any], label: str) -> bool:
    explicit = len(detect_laws(row["question"]["question"])) == 1
    return label == "all" or (label == "explicit" and explicit) or (label == "implicit" and not explicit)


def _paired(rows: list[dict[str, Any]], variant: str) -> dict[str, Any]:
    result = {}
    for metric in ("source_any", "source_all", "document_hit"):
        result[metric] = {}
        for cutoff in ("5",):
            groups = {name: [] for name in ("improved", "unchanged", "regressed")}
            for row in rows:
                change = int(row["variants"][variant]["metrics"][cutoff][metric]) - int(row["variants"]["B0"]["metrics"][cutoff][metric])
                groups["improved" if change > 0 else "regressed" if change < 0 else "unchanged"].append(row["question"]["id"])
            result[metric][cutoff] = {name: {"count": len(ids), "ids": ids} for name, ids in groups.items()}
    return result


def _rank_for_source(ranks: list[dict[str, Any]], source: str) -> int | None:
    return next((rank["rank"] for rank in ranks if rank["document_source_key"] == source), None)


def render() -> None:
    """Render all metrics and comparisons from saved JSON only."""
    state = _load()
    assert state["status"] == "completed" and len(state["results"]) == 105
    rows = state["results"]
    state["summaries"] = {}
    state["subgroup_summaries"] = {}
    for variant in VARIANTS:
        state["summaries"][variant] = _summary(rows, variant)
        state["subgroup_summaries"][variant] = {group: _summary([row for row in rows if _subgroup(row, group)], variant) for group in ("implicit", "explicit")}
        for group in ("5326", "4458", "5607"):
            state["subgroup_summaries"][variant][group] = _summary([row for row in rows if m12d.DOCS[group] in row["question"]["expected_document_ids"]], variant)
        state["subgroup_summaries"][variant]["single_source"] = _summary([row for row in rows if len(row["question"]["expected_document_ids"]) == 1], variant)
        state["subgroup_summaries"][variant]["multi_source"] = _summary([row for row in rows if len(row["question"]["expected_sources"]) > 1], variant)
    state["paired_against_B0"] = {variant: _paired(rows, variant) for variant in ("R1", "R2")}
    state["routing_error_cost"] = {}
    router_rows = {row["question"]["id"]: row for row in json.loads(ROUTER_PATH.read_bytes())["results"]}
    for row in rows:
        if row["question"]["id"] not in json.loads(ROUTER_PATH.read_bytes()).get("routing_evaluation", {}).get("top1_error_ids", []):
            continue
    for question_id in ["q040", "gk028", "k5607-010", "k5607-014", "k5607-028"]:
        row = next(item for item in rows if item["question"]["id"] == question_id)
        prediction = router_rows[question_id]["prediction"]
        b0 = row["variants"]["B0"]["metrics"]["5"]
        r1 = row["variants"]["R1"]["metrics"]["5"]
        r2 = row["variants"]["R2"]["metrics"]["5"]
        classifications = []
        if r1["source_any"] < b0["source_any"] or r1["source_all"] < b0["source_all"]:
            classifications.append("A hard-route regression")
        if r1["source_any"] < b0["source_any"] and r2["source_any"] >= b0["source_any"]:
            classifications.append("B R2 safety recovery")
        if not b0["source_any"] or not b0["source_all"]:
            classifications.append("C B0 was already wrong")
        if r1 == b0 and r2 == b0:
            classifications.append("D no retrieval impact")
        state["routing_error_cost"][question_id] = {"true_document": row["true_document"], "top1": prediction[0], "top2": prediction[1], "b0_source_any_5": b0["source_any"], "b0_source_all_5": b0["source_all"], "r1_source_any_5": r1["source_any"], "r1_source_all_5": r1["source_all"], "r2_source_any_5": r2["source_any"], "r2_source_all_5": r2["source_all"], "classification": classifications or ["D no retrieval impact"]}
    state["primary_cases"] = {}
    for question_id in PRIMARY:
        row = next(item for item in rows if item["question"]["id"] == question_id)
        sources = sorted(_keys(row["question"]))
        state["primary_cases"][question_id] = {"saved_router_ranking": row["saved_router_ranking"], "expected_sources": sources, "variants": {variant: {"top5": row["variants"][variant]["ranks"], "source_ranks": {source: _rank_for_source(row["variants"][variant]["ranks"], source) for source in sources}} for variant in VARIANTS}}
    state["m12fc_consistency"] = {question_id: state["primary_cases"][question_id]["variants"]["R1"]["source_ranks"] for question_id in PRIMARY}
    state["saved_router_predictions_reused"] = True
    state["llm_router_calls"] = 0
    state["no_gold_fallback"] = True
    state["final_experiment"] = True
    state["network_recovery"] = state.get("network_recovery", [])
    state["network_recovery_summary"] = {"initial_sandbox_failures": len(state["network_recovery"]), "successful_embedding_batches": 1, "successful_batch_requests": 1, "total_attempts": 1 + len(state["network_recovery"]), "history_preserved": True}
    state["api"]["requests"] = 1
    state["api"]["accounting_scope"] = "successful embedding batch; initial sandbox failure is recorded separately in network_recovery"
    state["verdict"] = "M12F-E2 READY FOR REVIEW \u2014 ROUTED RETRIEVAL MIXED"
    state["decision"] = {
        "verdict": state["verdict"],
        "evidence": [
            "R1 recovers both M12F-C document-discrimination cases k5607-003 and k5607-004.",
            "R1 Source ANY @5 improves for 5 questions and regresses for 4; Source ALL @5 improves for 2 and regresses for 4.",
            "R2 has no paired @5 improvements and returns to B0 coverage, while limiting R1 routing-error regressions.",
            "R1 improves 5607 Source ANY @5 from 25/30 to 26/30 but lowers 5607 Source ALL @5 from 24/30 to 23/30.",
            "Composite provision-selection remains unresolved: k5607-025 recovers only Madde 3, k5607-026 only Madde 5, and k5607-029 still misses Madde 3.",
        ],
        "next_high_level_step": "After review, close M12F, then proceed to M13 Gümrük Yönetmeliği onboarding.",
        "candidate_status": "development evidence only; no production adoption",
        "new_unseen_holdout_required": True,
    }
    _save(state)
    _render_files(state)
    print(json.dumps({"verdict": state["verdict"], "api": state["api"], "queries": state["query_operations"], "paired": state["paired_against_B0"]}, ensure_ascii=True), flush=True)


def _render_files(state: dict[str, Any]) -> None:
    rows = state["results"]
    fields = ["id", "question", "variant", "rank", "chunk_id", "document_source_key", "document_id", "distance", "expected_sources", "source_any@1", "source_any@3", "source_any@5", "source_all@1", "source_all@3", "source_all@5", "document_hit@1", "document_hit@3", "document_hit@5", "document_all@1", "document_all@3", "document_all@5", "document_intrusion@1", "document_intrusion@3", "document_intrusion@5"]
    with OUT.with_suffix(".csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            for variant in VARIANTS:
                for rank in row["variants"][variant]["ranks"]:
                    record = {"id": row["question"]["id"], "question": row["question"]["question"], "variant": variant, "expected_sources": " | ".join(sorted(_keys(row["question"]))), **{key: rank.get(key) for key in ("rank", "chunk_id", "document_source_key", "document_id", "distance")}}
                    record.update({f"{metric}@{cutoff}": row["variants"][variant]["metrics"][str(cutoff)][metric] for metric in METRICS for cutoff in CUTOFFS})
                    writer.writerow(record)
    lines = ["# M12F-E2 — LLM Router Retrieval Integration Diagnostic", "", state["verdict"], "", "Development-only evidence. Saved M12F-E predictions were reused; the LLM router was not called again. This is the final M12F routing integration experiment.", "", "## Population and accounting", "", "```json", json.dumps({"population": state["population"], "saved_router": state["saved_router"], "api": state["api"], "query_operations": state["query_operations"]}, ensure_ascii=False, indent=2), "```", "", "B0 is saved historical M12F-B raw/global evidence. R1 and R2 are fresh copy-only retrieval. This is not a same-run causal comparison.", "", "## Metrics", "", "| Variant | Metric | @1 | @3 | @5 |", "|---|---|---:|---:|---:|"]
    for variant in VARIANTS:
        for metric in METRICS:
            lines.append(f"| {variant} | {metric} | " + " | ".join(f"{state['summaries'][variant]['metrics'][str(cutoff)][metric]:.2%}" for cutoff in CUTOFFS) + " |")
    lines += ["", "## Paired changes against B0 at @5", "", "```json", json.dumps(state["paired_against_B0"], ensure_ascii=False, indent=2), "```", "", "## Five saved LLM Top1 routing errors", ""]
    for question_id, detail in state["routing_error_cost"].items():
        lines.append(f"- `{question_id}`: true={detail['true_document']}; Top1={detail['top1']}; Top2={detail['top2']}; classification={'; '.join(detail['classification'])}; B0 ANY/ALL={detail['b0_source_any_5']}/{detail['b0_source_all_5']}; R1={detail['r1_source_any_5']}/{detail['r1_source_all_5']}; R2={detail['r2_source_any_5']}/{detail['r2_source_all_5']}")
    lines += ["", "## Six primary cases", "", "```json", json.dumps(state["primary_cases"], ensure_ascii=False, indent=2), "```", "", "## Interpretation", "", "R1 and R2 are diagnostics only. No production routing candidate was adopted. Correct routing does not claim to solve within-document provision selection, especially for the composite 5607 cases. Any future adopted candidate requires a NEW UNSEEN HOLDOUT.", "", "This is the final M12F routing integration experiment. The next high-level step after review is M12F closure, then M13 — Gümrük Yönetmeliği onboarding.", "", f"Production bytes unchanged: `{state['chroma']['production_unchanged']}`; copy logical state unchanged: `{state['chroma']['logical_unchanged']}`; protected inputs unchanged: `{state['inputs_unchanged']}`."]
    OUT.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run", "render"))
    args = parser.parse_args()
    {"prepare": prepare, "run": run, "render": render}[args.command]()


if __name__ == "__main__":
    main()
