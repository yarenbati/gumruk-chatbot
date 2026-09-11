"""One-shot M12D benchmark using unchanged production retrieval on a verified copy."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import chromadb
from openai import OpenAI

from src import config, evaluate_documents as ev, evaluate_multilaw as legacy, retrieve
from scripts.build_m12d_5607_candidate import validate

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/evaluation"
JSON_PATH = REPORT / "m12d-three-source-retrieval.json"
CSV_PATH = REPORT / "m12d-three-source-retrieval.csv"
AUDIT_PATH = REPORT / "m12d-offline-audit.md"
FROZEN = ROOT / "evaluation/questions_5607.json"
CANDIDATE = ROOT / "evaluation/questions_5607.candidate.json"
DOCS = {"5326": "5326_kabahatler_kanunu", "4458": "4458_gumruk_kanunu",
        "5607": "5607_kacakcilikla_mucadele_kanunu"}
DISTRIBUTION = dict(zip(DOCS.values(), (53, 276, 46)))
HISTORICAL = ("tests/questions.json", "evaluation/questions_m9b.json", "evaluation/questions_4458.json")


def _hash(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {"size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def _tree(path: Path) -> dict[str, Any]:
    files = {p.relative_to(path).as_posix(): _hash(p) for p in sorted(path.rglob("*")) if p.is_file()}
    if not files:
        raise RuntimeError("Chroma directory contains no files")
    return files


def _write(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _questions() -> list[ev.DocumentQuestion]:
    payload = json.loads(FROZEN.read_text(encoding="utf-8"))
    # Preserve the approved annotation fields in the frozen file; project only
    # evaluator fields in memory, with no identity conversion for 5607.
    fields = ("id", "question", "expected_sources", "expected_document_ids")
    projected = {"source_identity_schema": payload["source_identity_schema"],
                 "questions": [{k: q[k] for k in fields} for q in payload["questions"]]}
    old5326 = [ev.adapt_legacy_question(q) for q in legacy.load_5326_questions()]
    old4458 = [ev.adapt_legacy_question(q) for q in legacy.load_4458_questions()]
    new = list(ev.dataset_from_dict(projected))
    assert (len(old5326), len(old4458), len(new)) == (45, 30, 30)
    questions = old5326 + old4458 + new
    assert len({q.id for q in questions}) == 105
    assert all(len(q.expected_document_ids) == 1 for q in questions)
    return questions


def _logical(collection: Any) -> dict[str, Any]:
    data = collection.get(include=["documents", "metadatas", "embeddings"])
    rows = sorted([[key, text, meta, vector.tolist()] for key, text, meta, vector in
                   zip(data["ids"], data["documents"], data["metadatas"], data["embeddings"])])
    return {"count": collection.count(),
            "distribution": dict(Counter(m["document_id"] for m in data["metadatas"])),
            "dimensions": sorted({len(v) for v in data["embeddings"]}),
            "sha256": hashlib.sha256(json.dumps(rows, sort_keys=True, ensure_ascii=False).encode()).hexdigest()}


def prepare() -> None:
    """Freeze approved bytes, record review, and verify a fresh unopened copy."""
    if JSON_PATH.exists():
        raise RuntimeError("Existing M12D report: refusing to replace or rerun")
    raw = CANDIDATE.read_bytes()
    payload = json.loads(raw)
    composition = validate(payload)
    assert [q["id"] for q in payload["questions"]] == [f"k5607-{i:03d}" for i in range(1, 31)]
    assert (composition["distinct_keys"], composition["normal_keys"], composition["gecici_keys"],
            composition["suffixed_keys"]) == (24, 21, 3, 1)
    if FROZEN.exists():
        assert FROZEN.read_bytes() == raw, "Existing frozen file differs; never overwrite"
    else:
        with FROZEN.open("xb") as handle:
            handle.write(raw)
    assert json.loads(FROZEN.read_bytes()) == payload
    questions = _questions()
    review = REPORT / "m12d-5607-question-review.csv"
    with review.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    assert len(rows) == 30
    for row, q in zip(rows, questions[-30:]):
        assert row["id"] == q.id and row["question"] == q.question
        assert set(row["expected_sources"].split(" | ")) == {str(k) for k in q.expected_sources}
        prior = row["review_status"]
        row["review_status"] = "project_human_review_passed"
        note = f"Phase A approved by project human reviewer in task instruction; previous status: {prior}. Legal expert validation not asserted."
        row["reviewer_notes"] = (row["reviewer_notes"] + " | " + note).strip(" |")
    with review.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    production = (ROOT / config.CHROMA_PATH).resolve()
    before = _tree(production)
    copy = Path(tempfile.mkdtemp(prefix="m12d-chroma-copy-")) / "chroma"
    shutil.copytree(production, copy)
    copied = _tree(copy)
    assert before == copied == _tree(production), "Copy byte verification failed"
    collection = chromadb.PersistentClient(path=str(copy)).get_collection(config.COLLECTION_NAME, embedding_function=None)
    logical = _logical(collection)
    assert logical["count"] == 375 and logical["distribution"] == DISTRIBUTION, "STOP: unexpected copy logical state"
    assert logical["dimensions"] == [1536]
    assert retrieve.distance_metric(collection) == "l2" and config.TOP_K == 5
    admission = json.loads((REPORT / "m12c-5607-indexing.json").read_text())
    assert config.EMBEDDING_MODEL == admission["embedding_model"]
    actual_keys = {ev.source_registry.source_key_from_metadata(m) for m in collection.get(include=["metadatas"])["metadatas"]}
    assert all(q.expected_sources <= actual_keys for q in questions)
    state = {"status": "prepared", "created_utc": datetime.now(timezone.utc).isoformat(),
             "frozen_5607": {**_hash(FROZEN), "question_count": 30, "source_identity_schema": payload["source_identity_schema"], "candidate_semantically_equal": True},
             "composition_5607": composition,
             "historical_files": {p: _hash(ROOT / p) for p in HISTORICAL},
             "retrieval_configuration": {"model": config.EMBEDDING_MODEL, "dimensions": 1536, "top_k": 5,
                 "distance_metric": "l2", "filter": None, "rerank": False, "query_expansion": False,
                 "max_retries": 0, "bm25": False, "rrf": False, "experiments": [], "source_key_deduplication": False},
             "chroma": {"production_path": str(production), "copy_path": str(copy), "production_files_before": before,
                 "copy_files_before_open": copied, "byte_equal_before_open": True, "logical_before": logical},
             "pre_run": {"5326": 45, "4458": 30, "5607": 30, "total": 105, "expected_query_embedding_calls": 105,
                 "embedding_model": config.EMBEDDING_MODEL, "expected_dimensions": 1536, "TOP_K": 5, "copy_logical_count": 375},
             "api": {"query_embedding_calls": 0, "successful_query_count": 0, "failed_query_count": 0,
                 "generation_calls": 0, "prompt_tokens": 0, "total_tokens": 0}, "results": []}
    _write(JSON_PATH, state)
    print(json.dumps(state["pre_run"], indent=2), flush=True)
    print(json.dumps(state["frozen_5607"], indent=2), flush=True)


class CountingEmbeddings:
    """Expose only the embedding endpoint, counting attempts with SDK retries off."""

    def __init__(self, endpoint: Any, api: dict[str, Any], dimensions: int) -> None:
        self.endpoint, self.api, self.dimensions = endpoint, api, dimensions

    def create(self, **kwargs: Any) -> Any:
        """Count a single attempt and reported tokens, without retrying failures."""
        assert len(kwargs["input"]) == 1
        self.api["query_embedding_calls"] += 1
        response = self.endpoint.create(**kwargs)
        for field in ("prompt_tokens", "total_tokens"):
            value = getattr(response.usage, field, None)
            self.api[field] = self.api[field] + value if self.api[field] is not None and value is not None else None
        assert all(len(item.embedding) == self.dimensions for item in response.data)
        return response


class EmbeddingOnlyClient:
    """Restricted injected client with no generation interface."""

    def __init__(self, api: dict[str, Any]) -> None:
        self.embeddings = CountingEmbeddings(OpenAI(api_key=config.OPENAI_API_KEY, max_retries=0).embeddings, api, 1536)


def analyze(result: ev.DocumentResult) -> dict[str, Any]:
    """Report overlapping source failure and document intrusion diagnostics."""
    q, ranks = result.question, result.ranks[:5]
    present = {r.document_source_key for r in ranks}
    missing = q.expected_sources - present
    return {"top1_document_id": ranks[0].document_id if ranks else None,
            "top1_document_expected": result.metrics[0].document_hit,
            "expected_document_top3": result.metrics[1].document_hit,
            "expected_document_top5": result.metrics[2].document_hit,
            "A_complete_top5_miss": not bool(q.expected_sources & present),
            "B_partial_multi_source_miss": bool(q.expected_sources & present) and bool(missing),
            "C_correct_document_wrong_articles": bool(missing) and result.metrics[2].document_hit,
            "D_wrong_document_intrusion": any(r.document_id not in q.expected_document_ids for r in ranks),
            "missing_sources": sorted(str(k) for k in missing),
            "madde_3_slots": [r.rank for r in ranks if r.document_source_key.document_id == DOCS["5607"] and r.document_source_key.article_type == "normal" and r.document_source_key.article_no == "3"],
            "madde_23_slots": [r.rank for r in ranks if r.document_source_key.document_id == DOCS["5607"] and r.document_source_key.article_type == "normal" and r.document_source_key.article_no == "23"]}


def _artifacts(state: dict[str, Any], results: list[ev.DocumentResult]) -> None:
    state["summary"] = ev.summarize(results)
    state["dataset_summaries"] = {law: ev.summarize([r for r in results if doc in r.question.expected_document_ids]) for law, doc in DOCS.items()}
    state["failure_ids"] = {name: [r["question"]["id"] for r in state["results"] if r["analysis"][name]] for name in
                            ("A_complete_top5_miss", "B_partial_multi_source_miss", "C_correct_document_wrong_articles", "D_wrong_document_intrusion")}
    state["wrong_document_top1_ids"] = [r["question"]["id"] for r in state["results"] if not r["analysis"]["top1_document_expected"]]
    state["top1_confusion"] = {law: {target: sum(r["analysis"]["top1_document_id"] == target for r in state["results"] if doc in r["question"]["expected_document_ids"]) for target in DOCS.values()} for law, doc in DOCS.items()}
    _write(JSON_PATH, state)
    fields = ["id", "question", "expected_sources", "expected_document_ids", "rank", "chunk_id", "document_source_key", "document_id", "distance", "article_id", "article_title", "source_path", "top1_document_id", "top1_document_expected", "expected_document_top3", "expected_document_top5", "A_complete_top5_miss", "B_partial_multi_source_miss", "C_correct_document_wrong_articles", "D_wrong_document_intrusion", "missing_sources"]
    fields += [f"{metric}@{k}" for metric in ("source_any", "source_all", "document_hit", "document_all", "document_intrusion") for k in (1, 3, 5)]
    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in state["results"]:
            q = row["question"]
            base = {"id": q["id"], "question": q["question"], "expected_sources": " | ".join(str(ev.source_identity.DocumentSourceKey.from_dict(s)) for s in q["expected_sources"]), "expected_document_ids": " | ".join(q["expected_document_ids"])}
            base.update({k: v for k, v in row["analysis"].items() if k in fields})
            base["missing_sources"] = " | ".join(base["missing_sources"])
            base.update({f"{m}@{k}": row["metrics"][str(k)][m] for m in ("source_any", "source_all", "document_hit", "document_all", "document_intrusion") for k in (1, 3, 5)})
            for rank in row["ranks"]:
                evidence = {k: v for k, v in rank.items() if k in fields}
                evidence.update({k: rank["metadata"].get(k) for k in ("article_id", "article_title", "source_path")})
                writer.writerow({**base, **evidence})
    lines = ["# M12D three-source offline audit", "", f"Status: {state['status']}", "", "NO retrieval optimization was performed", "",
             "Project human approval: Phase A APPROVED in task instruction. Legal expert validation is not asserted.",
             "Frozen 5607 bytes are unchanged from the approved candidate; evaluator-only field projection occurs in memory.",
             "Historical 5326/4458 use only existing loaders and the explicit reviewed legacy adapter; 5607 uses document-source-v1 directly. CURRENT_LEGACY_REGISTRY is unchanged.", ""]
    for title, item in (("Frozen 5607", state["frozen_5607"]), ("Dataset composition", state["composition_5607"]), ("Pre-run accounting", state["pre_run"]), ("Retrieval configuration", state["retrieval_configuration"]), ("API accounting", state["api"])):
        lines += [f"## {title}", "", "```json", json.dumps(item, ensure_ascii=False, indent=2), "```", ""]
    lines += ["## Chroma copy-first verification", "", f"Production: `{state['chroma']['production_path']}`. Temporary copy: `{state['chroma']['copy_path']}`.",
              "All relative file names, sizes, and SHA-256 values were equal before opening the copy. Full manifests are in the JSON artifact.",
              f"Logical state before: `{json.dumps(state['chroma']['logical_before'])}`.",
              f"Post-run production bytes unchanged: {state['chroma'].get('production_unchanged')}; copy logical state unchanged: {state['chroma'].get('logical_unchanged')}.", ""]
    for label, summary in list(state["dataset_summaries"].items()) + [("combined", state["summary"])]:
        lines += [f"## {label} metrics", "", f"Questions: {summary['overall']['count']}; single-source: {summary['single_source']['count']}; multi-source: {summary['multi_source']['count']}. All expected-document sets are single-document.", "", "| Metric | @1 | @3 | @5 |", "|---|---:|---:|---:|"]
        for metric in ("source_any", "source_all", "document_hit", "document_all", "document_intrusion"):
            values = [summary["overall"]["metrics"][str(k)][metric] for k in (1, 3, 5)]
            lines.append("| " + metric + " | " + " | ".join(f"{v:.2%}" if v is not None else "N/A" for v in values) + " |")
        lines += ["", "Single-source and multi-source metrics are separately available in the JSON dataset summaries.", ""]
    lines += ["## Wrong-document Top1", "", ", ".join(state["wrong_document_top1_ids"]) or "None", "", "```json", json.dumps(state["top1_confusion"], indent=2), "```", "",
              "## Top-5 source failures (overlap retained)", "", "A: no expected source. B: some but not all required sources. C: source coverage fails while the expected document is present. D: any wrong-document Top-5 slot, even if all sources are covered. C overlaps A/B; D may overlap any category. Intrusion is diagnostic, not a legal-error judgment.", ""]
    for name, ids in state["failure_ids"].items():
        lines += [f"- {name}: {', '.join(ids) or 'None'}"]
    lines += ["", "## 5607: Madde 16/A, Geçici, multi-source, Madde 3/23", "", "Cutoffs retain repeated source slots. Source coverage naturally uses sets; the ranking is never deduplicated.", "", "| ID | Expected sources | ANY @1/3/5 | ALL @1/3/5 | Missing @5 | Madde 3 slots | Madde 23 slots |", "|---|---|---|---|---|---|---|"]
    for r in state["results"]:
        q = r["question"]
        if DOCS["5607"] not in q["expected_document_ids"]:
            continue
        keys = q["expected_sources"]
        if q["id"] == "k5607-017" or len(keys) > 1 or any(s["article_type"] == "gecici" or s["article_no"] in ("3", "23", "16/A") for s in keys):
            flags = lambda metric: "/".join(str(int(r["metrics"][str(k)][metric])) for k in (1, 3, 5))
            labels = ", ".join(s["article_type"] + "/" + s["article_no"] for s in keys)
            a = r["analysis"]
            lines.append(f"| {q['id']} | {labels} | {flags('source_any')} | {flags('source_all')} | {', '.join(a['missing_sources']) or 'None'} | {a['madde_3_slots']} | {a['madde_23_slots']} |")
    lines += ["", "### Multi-chunk slot duplication across all 105 questions", ""]
    for article in (3, 23):
        duplicates = {r["question"]["id"]: r["analysis"][f"madde_{article}_slots"] for r in state["results"] if len(r["analysis"][f"madde_{article}_slots"]) > 1}
        lines += [f"Madde {article}: `{json.dumps(duplicates)}`", ""]
    if state.get("error"):
        lines += ["## Benchmark issue", "", state["error"], "No replacement run was attempted.", ""]
    if state.get("verification"):
        lines += ["## Offline verification", "", "```json", json.dumps(state["verification"], indent=2), "```", ""]
    AUDIT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run() -> None:
    """Execute once; checkpoint every question and stop on the first failure."""
    state = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    assert state["status"] == "prepared", "Run already attempted; replacement requires explicit review"
    assert _hash(FROZEN) == {k: state["frozen_5607"][k] for k in ("size_bytes", "sha256")}
    assert all(_hash(ROOT / p) == fingerprint for p, fingerprint in state["historical_files"].items())
    assert _tree(Path(state["chroma"]["production_path"])) == state["chroma"]["production_files_before"]
    assert config.TOP_K == 5 and config.EMBEDDING_MODEL == state["retrieval_configuration"]["model"]
    collection = chromadb.PersistentClient(path=state["chroma"]["copy_path"]).get_collection(config.COLLECTION_NAME, embedding_function=None)
    assert _logical(collection) == state["chroma"]["logical_before"]
    assert retrieve.distance_metric(collection) == "l2"
    questions = _questions()
    print(json.dumps(state["pre_run"], indent=2), flush=True)
    state["status"] = "running"
    _write(JSON_PATH, state)
    results: list[ev.DocumentResult] = []
    active_id = None
    try:
        client = EmbeddingOnlyClient(state["api"])
        for q in questions:
            active_id = q.id
            outcome = retrieve.retrieve(q.question, collection=collection, client=client,
                                        model=config.EMBEDDING_MODEL, top_k=5, where=None)
            assert outcome.returned_count == 5 and outcome.distance_metric == "l2"
            result = ev.evaluate_retrieved(q, outcome.results)
            results.append(result)
            row = result.to_dict()
            for rank, chunk in zip(row["ranks"], outcome.results):
                # Canonical text is not duplicated into tracked reports; metadata,
                # distance and exact chunk text hash make evidence auditable.
                rank.update(distance=chunk.distance, metadata=chunk.metadata,
                            text_sha256=hashlib.sha256(chunk.text.encode()).hexdigest())
            row["analysis"] = analyze(result)
            row["latency_ms"] = outcome.latency_ms
            state["results"].append(row)
            state["api"]["successful_query_count"] += 1
            _write(JSON_PATH, state)
            print(f"Completed {q.id} ({len(results)}/105)", flush=True)
        assert state["api"]["query_embedding_calls"] == 105
        state["status"] = "completed"
    except Exception as exc:
        state["status"] = "blocked"
        state["api"]["failed_query_count"] = 1 if active_id else 0
        state["failed_question_id"] = active_id
        state["error"] = f"{type(exc).__name__}: {str(exc)}"
        print(f"STOP: {state['error']}", flush=True)
    finally:
        state["chroma"]["production_files_after"] = _tree(Path(state["chroma"]["production_path"]))
        state["chroma"]["production_unchanged"] = state["chroma"]["production_files_after"] == state["chroma"]["production_files_before"]
        state["chroma"]["logical_after"] = _logical(collection)
        state["chroma"]["logical_unchanged"] = state["chroma"]["logical_after"] == state["chroma"]["logical_before"]
        state["frozen_and_historical_unchanged"] = _hash(FROZEN)["sha256"] == state["frozen_5607"]["sha256"] and all(_hash(ROOT / p) == h for p, h in state["historical_files"].items())
        if not all((state["chroma"]["production_unchanged"], state["chroma"]["logical_unchanged"], state["frozen_and_historical_unchanged"])):
            state["status"] = "blocked"
            state["error"] = "Post-run immutable-state verification failed"
        _artifacts(state, results)
    if state["status"] != "completed":
        raise SystemExit(1)


def audit() -> None:
    """Recheck saved evidence and regenerate reports offline, without retrieval."""
    state = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    assert state["status"] == "completed"
    questions = _questions()
    assert [q.id for q in questions] == [r["question"]["id"] for r in state["results"]]
    results = []
    for q, row in zip(questions, state["results"]):
        assert q.to_dict() == row["question"]
        assert len(row["ranks"]) == 5
        ranks = [ev.DocumentRank(r["rank"], r["chunk_id"], ev.source_identity.DocumentSourceKey.parse(r["document_source_key"]), r["document_id"], r["legislation_number"]) for r in row["ranks"]]
        for rank, raw in zip(ranks, row["ranks"]):
            assert ev.source_registry.source_key_from_metadata(raw["metadata"]) == rank.document_source_key
        result = ev.evaluate_question(q, ranks)
        assert result.to_dict()["metrics"] == row["metrics"]
        assert analyze(result) == row["analysis"]
        results.append(result)
    assert ev.summarize(results) == state["summary"]
    assert FROZEN.read_bytes() == CANDIDATE.read_bytes()
    assert _hash(FROZEN)["sha256"] == state["frozen_5607"]["sha256"]
    assert all(_hash(ROOT / p) == h for p, h in state["historical_files"].items())
    assert _tree(Path(state["chroma"]["production_path"])) == state["chroma"]["production_files_before"]
    assert state["api"]["query_embedding_calls"] == state["api"]["successful_query_count"] == 105
    assert state["api"]["failed_query_count"] == state["api"]["generation_calls"] == 0
    state.setdefault("verification", {}).update(saved_rank_slots=525, saved_question_metrics_recomputed=True,
        production_bytes_rechecked=True, frozen_and_historical_hashes_rechecked=True)
    _artifacts(state, results)
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 525 and len({r["id"] for r in rows}) == 105
    print("Offline audit passed: 105 questions, 525 ranked slots, saved metrics and immutable hashes verified.")


def main() -> None:
    """Separate offline preparation from the explicitly invoked one-shot run."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "run", "audit"))
    args = parser.parse_args()
    {"prepare": prepare, "run": run, "audit": audit}[args.phase]()


if __name__ == "__main__":
    main()
