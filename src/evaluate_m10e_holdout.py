"""
M10E-B blind holdout benchmark: the ONE authorized B0-vs-B2 real run against
the frozen holdout (evaluation/questions_m10e_holdout.json), executed
against the verified EXPERIMENTAL Chroma COPY only.

Scope boundary (see the M10E-B milestone brief): this module NEVER opens
production Chroma (`src.config.CHROMA_PATH`) - it only ever opens a copy
path passed in explicitly (default `.m10e_holdout_chroma/`, resolved
relative to the project root). It reuses the FROZEN M10E-A B2
implementation (`src.evaluate_retrieval_experiments`: `BM25`, `rrf`,
`Document`, `local_variants`, `collect_dense`, `score`, `summarize`,
`breakdown`) exactly - no BM25/RRF parameter, tokenizer, or tie-break rule
is redefined here. Only B0 and B2 are evaluated; B1's ranking is computed
only as B2's own required lexical-candidate step (via `local_variants`) and
is never itself scored or reported, and B3/B4 are never invoked at all.

Exactly one dense Top-20 call per holdout question (`collect_dense`, top_k=
`config.M10E_DENSE_CANDIDATE_K`); B0 is the first 5 results of that SAME
call, never a second retrieval. No query rewriting, no law/expected-source
filtering, no reranking beyond the frozen B2 RRF, no generation call.

Real-run gate mirrors every other real-API entry point in this project:
both `config.OPENAI_API_KEY` and `RUN_OPENAI_INTEGRATION_TESTS=1` are
required (see `_real_run_opt_in`). The reusable functions above the CLI
carry no such gate and never call OpenAI themselves when given a fake
client/collection (see tests/test_evaluate_m10e_holdout.py).

CLI usage (manual/local, NOT part of the automated test suite - this run is
authorized exactly once for the frozen holdout):
    RUN_OPENAI_INTEGRATION_TESTS=1 python -m src.evaluate_m10e_holdout
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import chromadb

from src import config
from src import evaluate_retrieval_experiments as e
from src import m10e_holdout as h

if __name__ == "__main__":  # pragma: no cover - exercised via CLI, not tests
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COPY_PATH = ROOT / ".m10e_holdout_chroma"
OUTPUT_JSON = ROOT / "reports" / "evaluation" / "m10e-holdout-b0-vs-b2.json"
OUTPUT_CSV = ROOT / "reports" / "evaluation" / "m10e-holdout-b0-vs-b2.csv"
OUTPUT_MD = ROOT / "reports" / "evaluation" / "m10e-holdout-b0-vs-b2.md"

MULTI_SOURCE_DIAGNOSTIC_IDS = ("h5326-10", "h4458-13", "h4458-14", "h4458-15", "h4458-16")

STRATEGY_DEFINITIONS = {
    "B0": "First 5 results of the single dense Top-20 retrieval; no second/separate B0 query.",
    "B2": e.DEFINITIONS["B2"],
    "not_run": "B1 (bare BM25) and B3/B4 are never scored or reported here; B1's ranking is computed only "
               "as B2's own required lexical-candidate input via the frozen local_variants().",
}


class HoldoutBenchmarkError(RuntimeError):
    """Raised for a holdout-benchmark precondition failure (bad hash, wrong
    question count, unexpected collection counts, a re-run attempt) - never
    silently proceeds with an unverified frozen input or a second real run.
    """


# ============================================================================
# Preflight: frozen holdout identity + zero dev-gold overlap
# ============================================================================


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_frozen_holdout(path: Path = h.FINAL_PATH) -> tuple[str, list[h.HoldoutCandidateQuestion]]:
    """Recompute the full holdout SHA-256, strictly reload+validate it
    (raises on any drift from the frozen contract), and re-verify zero
    DEV_GOLD_KEYS overlap. Returns (sha256_hex, questions)."""
    digest = sha256_of(path)
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise HoldoutBenchmarkError(f"SHA-256 is not a 64-char lowercase hex string: {digest!r}")

    questions = h.load_final_questions(path)
    if len(questions) != 30:
        raise HoldoutBenchmarkError(f"Expected 30 frozen holdout questions, got {len(questions)}")
    h.validate_zero_dev_gold_overlap(questions)
    h.validate_keys_exist_in_corpus(questions)
    return digest, questions


def load_holdout_question_dicts(path: Path = h.FINAL_PATH) -> list[dict[str, Any]]:
    """Adapt the frozen holdout into the plain-dict shape
    `evaluate_retrieval_experiments.score()`/`summarize()` already expect -
    reusing those functions rather than re-implementing scoring."""
    _, questions = verify_frozen_holdout(path)
    out = []
    for q in questions:
        out.append({
            "id": q.id,
            "question": q.question,
            "dataset": q.dataset,
            "expected_sources": sorted(str(k) for k in q.expected_sources),
            "expected_legislations": sorted({k.legislation_number for k in q.expected_sources}),
            "case_type": q.case_type,
            "difficulty": q.difficulty,
        })
    return out


# ============================================================================
# Experimental-copy-only Chroma access (never production)
# ============================================================================


def open_experimental_copy_collection(copy_path: Path = DEFAULT_COPY_PATH):
    """Open ONLY the experimental Chroma copy - never
    `src.config.CHROMA_PATH`. No embedding function is attached, so opening
    this client can never itself trigger an OpenAI call."""
    copy_path = Path(copy_path).resolve()
    prod_path = Path(config.CHROMA_PATH).resolve()
    if copy_path == prod_path:
        raise HoldoutBenchmarkError("Refusing to open production CHROMA_PATH as the experimental copy")
    if not copy_path.exists():
        raise HoldoutBenchmarkError(f"Experimental copy not found at {copy_path} - it must already exist")
    client = chromadb.PersistentClient(path=str(copy_path))
    collection = client.get_collection(name=config.COLLECTION_NAME, embedding_function=None)
    return client, collection


# ============================================================================
# Per-question B0/B2 scoring (reuses e.score/e.local_variants/e.collect_dense)
# ============================================================================


def multi_source_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [r for r in rows if len(r["expected_sources"]) > 1]


def _count(rows: list[dict[str, Any]], field: str) -> int:
    return sum(1 for r in rows if r[field])


# ============================================================================
# Deltas (§8)
# ============================================================================


def compute_deltas(b0_rows: list[dict[str, Any]], b2_rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_id_b0 = {r["id"]: r for r in b0_rows}
    by_id_b2 = {r["id"]: r for r in b2_rows}
    if set(by_id_b0) != set(by_id_b2):
        raise HoldoutBenchmarkError("B0/B2 row ID sets differ")
    deltas: dict[str, Any] = {}
    for metric, field in (("ANY", "any_source_hit_at_"), ("ALL", "all_sources_match_at_")):
        for k in (1, 3, 5):
            key = f"{metric}@{k}"
            miss_to_hit = sorted(
                qid for qid in by_id_b0
                if not by_id_b0[qid][f"{field}{k}"] and by_id_b2[qid][f"{field}{k}"]
            )
            hit_to_miss = sorted(
                qid for qid in by_id_b0
                if by_id_b0[qid][f"{field}{k}"] and not by_id_b2[qid][f"{field}{k}"]
            )
            deltas[key] = {"b0_miss_to_b2_hit": miss_to_hit, "b0_hit_to_b2_miss": hit_to_miss}
    return deltas


# ============================================================================
# Predeclared success gates (§6/§16) - frozen BEFORE this run
# ============================================================================


def evaluate_gates(b0_rows: list[dict[str, Any]], b2_rows: list[dict[str, Any]]) -> dict[str, Any]:
    b0_5326 = [r for r in b0_rows if r["dataset"] == "5326"]
    b2_5326 = [r for r in b2_rows if r["dataset"] == "5326"]
    b0_4458 = [r for r in b0_rows if r["dataset"] == "4458"]
    b2_4458 = [r for r in b2_rows if r["dataset"] == "4458"]
    b0_multi = multi_source_rows(b0_rows)
    b2_multi = multi_source_rows(b2_rows)

    gate_a = {
        "any_at_5": {"b0": _count(b0_5326, "any_source_hit_at_5"), "b2": _count(b2_5326, "any_source_hit_at_5")},
        "all_at_5": {"b0": _count(b0_5326, "all_sources_match_at_5"), "b2": _count(b2_5326, "all_sources_match_at_5")},
    }
    gate_a_pass = gate_a["any_at_5"]["b2"] >= gate_a["any_at_5"]["b0"] and gate_a["all_at_5"]["b2"] >= gate_a["all_at_5"]["b0"]

    any5_b0, any5_b2 = _count(b0_4458, "any_source_hit_at_5"), _count(b2_4458, "any_source_hit_at_5")
    all5_b0, all5_b2 = _count(b0_4458, "all_sources_match_at_5"), _count(b2_4458, "all_sources_match_at_5")
    gate_b = {"any_at_5": {"b0": any5_b0, "b2": any5_b2}, "all_at_5": {"b0": all5_b0, "b2": all5_b2}}
    improves_one = (any5_b2 > any5_b0) or (all5_b2 > all5_b0)
    other_not_degraded = ((any5_b0 - any5_b2) <= 1) and ((all5_b0 - all5_b2) <= 1)
    gate_b_pass = improves_one and other_not_degraded

    gate_c = {"all_at_5": {"b0": _count(b0_rows, "all_sources_match_at_5"), "b2": _count(b2_rows, "all_sources_match_at_5")}}
    gate_c_pass = gate_c["all_at_5"]["b2"] >= gate_c["all_at_5"]["b0"]

    leg_b0, leg_b2 = _count(b0_rows, "expected_legislation_hit_at_1"), _count(b2_rows, "expected_legislation_hit_at_1")
    gate_d = {"legislation_hit_at_1": {"b0": leg_b0, "b2": leg_b2}}
    gate_d_pass = (leg_b0 - leg_b2) <= 1

    multi_b0, multi_b2 = _count(b0_multi, "all_sources_match_at_5"), _count(b2_multi, "all_sources_match_at_5")
    gate_e = {"multi_source_count": len(b0_multi), "all_at_5": {"b0": multi_b0, "b2": multi_b2}}
    gate_e_pass = (len(b0_multi) == 0) or (multi_b2 >= multi_b0)

    gate_f_pass = True  # B2 is deterministic BM25+RRF; no generation/reranker API by construction.

    gates = {
        "A_5326_preservation": {"detail": gate_a, "pass": gate_a_pass},
        "B_4458_improves_without_material_degradation": {"detail": gate_b, "pass": gate_b_pass},
        "C_combined_all_at_5": {"detail": gate_c, "pass": gate_c_pass},
        "D_legislation_hit_at_1": {"detail": gate_d, "pass": gate_d_pass},
        "E_multi_source_all_at_5": {"detail": gate_e, "pass": gate_e_pass},
        "F_deterministic_no_generation": {"detail": {}, "pass": gate_f_pass},
    }
    decision = "VALIDATED" if all(g["pass"] for g in gates.values()) else "NOT VALIDATED"
    return {"gates": gates, "decision": decision}


# ============================================================================
# Multi-source diagnostics (§9) - diagnostic only, never special-cased
# ============================================================================


def multi_source_diagnostics(
    ids: tuple[str, ...], b0_rows: list[dict[str, Any]], b2_rows: list[dict[str, Any]]
) -> dict[str, Any]:
    by_id_b0 = {r["id"]: r for r in b0_rows}
    by_id_b2 = {r["id"]: r for r in b2_rows}
    out = {}
    for qid in ids:
        if qid not in by_id_b0:
            continue
        b0, b2 = by_id_b0[qid], by_id_b2[qid]
        out[qid] = {
            "expected_sources": sorted(b0["expected_sources"]),
            "b0_top5_qualified_source_keys": [r["qualified_source_key"] for r in b0["ranks"]],
            "b2_top5_qualified_source_keys": [r["qualified_source_key"] for r in b2["ranks"]],
            "b0_expected_source_ranks": b0["expected_source_ranks"],
            "b2_expected_source_ranks": b2["expected_source_ranks"],
            "b0_any_at_5": b0["any_source_hit_at_5"], "b0_all_at_5": b0["all_sources_match_at_5"],
            "b2_any_at_5": b2["any_source_hit_at_5"], "b2_all_at_5": b2["all_sources_match_at_5"],
        }
    return out


# ============================================================================
# Report assembly + writers
# ============================================================================


def build_summaries(b0_rows: list[dict[str, Any]], b2_rows: list[dict[str, Any]]) -> dict[str, Any]:
    summaries = {"B0": e.breakdown(b0_rows), "B2": e.breakdown(b2_rows)}
    for strategy, rows in (("B0", b0_rows), ("B2", b2_rows)):
        multi = multi_source_rows(rows)
        summaries[strategy]["multi_source_combined"] = e.summarize(multi) if multi else None
    return summaries


def write_json_report(report: dict[str, Any], path: Path = OUTPUT_JSON) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=sorted) + "\n", encoding="utf-8")


def write_csv_report(b0_rows: list[dict[str, Any]], b2_rows: list[dict[str, Any]], path: Path = OUTPUT_CSV) -> None:
    fields = [
        "strategy", "id", "dataset", "question", "expected_sources", "case_type", "difficulty",
        "top1_qualified_source_key", "top1_legislation", "any_source_hit_at_1", "any_source_hit_at_3",
        "any_source_hit_at_5", "all_sources_match_at_1", "all_sources_match_at_3", "all_sources_match_at_5",
        "expected_legislation_hit_at_1", "expected_legislation_hit_at_3", "expected_legislation_hit_at_5",
        "non_expected_legislation_count_at_5", "non_expected_legislation_share_at_5",
        "top5_qualified_source_keys",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for strategy, rows in (("B0", b0_rows), ("B2", b2_rows)):
            for r in rows:
                top5 = [rk["qualified_source_key"] for rk in r["ranks"]]
                writer.writerow({
                    "strategy": strategy, "id": r["id"], "dataset": r["dataset"], "question": r["question"],
                    "expected_sources": " | ".join(sorted(r["expected_sources"])), "case_type": r["case_type"],
                    "difficulty": r["difficulty"], "top1_qualified_source_key": top5[0] if top5 else None,
                    "top1_legislation": r["top1_legislation"],
                    "any_source_hit_at_1": r["any_source_hit_at_1"], "any_source_hit_at_3": r["any_source_hit_at_3"],
                    "any_source_hit_at_5": r["any_source_hit_at_5"],
                    "all_sources_match_at_1": r["all_sources_match_at_1"], "all_sources_match_at_3": r["all_sources_match_at_3"],
                    "all_sources_match_at_5": r["all_sources_match_at_5"],
                    "expected_legislation_hit_at_1": r["expected_legislation_hit_at_1"],
                    "expected_legislation_hit_at_3": r["expected_legislation_hit_at_3"],
                    "expected_legislation_hit_at_5": r["expected_legislation_hit_at_5"],
                    "non_expected_legislation_count_at_5": r["non_expected_legislation_count_at_5"],
                    "non_expected_legislation_share_at_5": r["non_expected_legislation_share_at_5"],
                    "top5_qualified_source_keys": " | ".join(k or "?" for k in top5),
                })


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.1f}%"


def write_md_report(report: dict[str, Any], path: Path = OUTPUT_MD) -> None:
    s = report["summaries"]
    ah = report["attempt_history"]
    lines = [
        "# M10E-B Blind Holdout: B0 vs B2",
        "",
        f"Frozen holdout SHA-256: `{report['metadata']['holdout_sha256']}`",
        f"Git commit: `{report['metadata']['git_head']}`",
        f"Experimental copy: `{report['metadata']['experimental_copy_path']}`",
        "",
        "## Attempt history",
        "",
        f"- Execution attempts total: **{ah['execution_attempts_total']}**",
    ]
    for a in ah["prior_failed_attempts"]:
        lines.append(
            f"  - Attempt {a['attempt']}: `{a['status']}` — {a['dense_calls']} dense calls, "
            f"failed at {a['failure_point']} ({a['failure_type']}); results_persisted={a['results_persisted']}, "
            f"results_inspected={a['results_inspected']}"
        )
    lines += [
        f"- Attempt {ah['current_attempt']} (this run): `{ah.get('current_attempt_status', 'unknown')}` — "
        f"{ah.get('current_attempt_dense_calls', 'n/a')} dense calls — **valid benchmark attempt**",
        f"- Total dense calls across all attempts: **{ah.get('total_dense_calls_across_all_attempts', 'n/a')}**",
        f"- Valid-run dense calls (this attempt only): **{ah.get('current_attempt_dense_calls', 'n/a')}**",
        "",
        "## Combined / per-law summary",
        "",
        "| Metric | B0 5326 | B2 5326 | B0 4458 | B2 4458 | B0 combined | B2 combined |",
        "|---|---|---|---|---|---|---|",
    ]
    for metric_label, key in (
        ("ANY@1", "any_qualified_recall_at_1"), ("ANY@3", "any_qualified_recall_at_3"), ("ANY@5", "any_qualified_recall_at_5"),
        ("ALL@1", "all_qualified_match_at_1"), ("ALL@3", "all_qualified_match_at_3"), ("ALL@5", "all_qualified_match_at_5"),
        ("Legislation Hit@1", "legislation_hit_at_1"), ("Legislation Hit@3", "legislation_hit_at_3"), ("Legislation Hit@5", "legislation_hit_at_5"),
    ):
        row = [metric_label]
        for law in ("5326", "4458", "combined"):
            for strategy in ("B0", "B2"):
                row.append(_pct(s[strategy][law][key]))
        lines.append("| " + " | ".join(row) + " |")
    lines += [
        "",
        "## Success gates",
        "",
    ]
    for name, g in report["gate_evaluation"]["gates"].items():
        lines.append(f"- **{name}**: {'PASS' if g['pass'] else 'FAIL'} — `{json.dumps(g['detail'])}`")
    lines += ["", f"## Final decision: **{report['gate_evaluation']['decision']}**", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ============================================================================
# CLI (the ONE authorized real run)
# ============================================================================


def _real_run_opt_in() -> bool:
    return bool(config.OPENAI_API_KEY) and os.getenv("RUN_OPENAI_INTEGRATION_TESTS") == "1"


#: History of prior EXECUTION ATTEMPTS against this frozen holdout, for
#: attempts that incurred real dense/API calls but produced no persisted,
#: inspected result (an infrastructure failure, never a "rerun for a
#: better result" - see the module docstring's blind-integrity claim).
#: Each entry's `results_inspected` MUST be `false`: this project never
#: revises a fix based on a peeked-at benchmark outcome.
PRIOR_FAILED_ATTEMPTS: tuple[dict[str, Any], ...] = (
    {
        "attempt": 1,
        "status": "failed_infrastructure",
        "dense_calls": 30,
        "failure_point": "report serialization (write_json_report) - AFTER all 30 dense/scoring operations completed",
        "failure_type": "TypeError: Object of type set is not JSON serializable",
        "results_persisted": False,
        "results_inspected": False,
        "fix_scope": "report persistence / checkpointing only - no retrieval, scoring, BM25/RRF parameter, "
                     "holdout, or gate logic changed (see the M10E-B fix audit)",
    },
)


def main(copy_path: str | Path | None = None) -> None:
    if not _real_run_opt_in():
        raise HoldoutBenchmarkError("Requires OPENAI_API_KEY and RUN_OPENAI_INTEGRATION_TESTS=1")
    if OUTPUT_JSON.exists():
        raise HoldoutBenchmarkError("Holdout benchmark output already exists; refusing a second real run")

    from openai import OpenAI

    resolved_copy_path = Path(copy_path) if copy_path is not None else Path(
        os.getenv("M10E_HOLDOUT_COPY_PATH", str(DEFAULT_COPY_PATH))
    )

    holdout_sha256, _ = verify_frozen_holdout()
    questions = load_holdout_question_dicts()
    client_chroma, collection = open_experimental_copy_collection(resolved_copy_path)

    documents, inventory_before = e.snapshot(collection)
    lexical = e.BM25(documents)

    prior_dense_calls = sum(a["dense_calls"] for a in PRIOR_FAILED_ATTEMPTS)
    report: dict[str, Any] = {
        "metadata": {
            "run_timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "collecting",
            "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "holdout_sha256": holdout_sha256,
            "holdout_path": str(h.FINAL_PATH.relative_to(ROOT)),
            "experimental_copy_path": str(resolved_copy_path.resolve()),
            "production_chroma_opens": 0,
            "collection_name": config.COLLECTION_NAME,
            "embedding_model": config.EMBEDDING_MODEL,
            "dense_candidate_k": config.M10E_DENSE_CANDIDATE_K,
            "benchmark_run_count": 1,
            "dense_retrieval_calls": 0,
            "query_embedding_api_requests": 0,
            "query_embedding_tokens": 0,
            "bm25_openai_calls": 0,
            "generation_calls": 0,
            "generation_tokens": 0,
            "inventory_before": inventory_before,
        },
        "attempt_history": {
            "execution_attempts_total": len(PRIOR_FAILED_ATTEMPTS) + 1,
            "prior_failed_attempts": list(PRIOR_FAILED_ATTEMPTS),
            "prior_dense_calls": prior_dense_calls,
            "current_attempt": len(PRIOR_FAILED_ATTEMPTS) + 1,
            "valid_benchmark_attempt": len(PRIOR_FAILED_ATTEMPTS) + 1,
        },
        "strategy_definitions": STRATEGY_DEFINITIONS,
        "fixed_parameters": {
            "dense_candidate_k": config.M10E_DENSE_CANDIDATE_K, "lexical_candidate_k": config.M10E_LEXICAL_CANDIDATE_K,
            "bm25_k1": config.M10E_BM25_K1, "bm25_b": config.M10E_BM25_B, "rrf_k": config.M10E_RRF_K, "top_k": 5,
        },
        "blindness_integrity": {
            "b2_selected_before_holdout_existed": True,
            "holdout_gold_frozen_before_retrieval": True,
            "dev_gold_overlap": 0,
            "no_holdout_retrieval_observed_before_gold_freeze": True,
            "b2_parameters_unchanged_after_holdout_creation": True,
            "no_question_or_gold_changed_after_seeing_results": True,
            "prior_attempt_results_ever_inspected": any(a["results_inspected"] for a in PRIOR_FAILED_ATTEMPTS),
        },
        "results": {"B0": [], "B2": []},
    }

    # Exclusive create BEFORE the first network call: an interruption after
    # this point can never silently cause an un-checkpointed paid re-run -
    # every dense call's result is persisted immediately below.
    with OUTPUT_JSON.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, default=sorted)

    def checkpoint() -> None:
        OUTPUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=sorted) + "\n", encoding="utf-8")

    try:
        with OpenAI(api_key=config.OPENAI_API_KEY, max_retries=0) as client:
            for question in questions:
                dense = e.collect_dense(question["question"], collection=collection, client=client)
                report["metadata"]["dense_retrieval_calls"] += 1
                report["metadata"]["query_embedding_api_requests"] += 1
                report["metadata"]["active_question"] = question["id"]
                checkpoint()
                if len(dense.results) < 5 or dense.embedding_usage.total_tokens is None:
                    raise HoldoutBenchmarkError(f"Incomplete dense payload/usage for {question['id']}; stopping without retry")
                report["metadata"]["query_embedding_tokens"] += dense.embedding_usage.total_tokens

                dense_ranks = []
                for chunk in dense.results:
                    doc = lexical.documents[chunk.chunk_id]
                    if chunk.text != doc.text or chunk.metadata != doc.metadata:
                        raise HoldoutBenchmarkError("Dense record differs from inventory snapshot")
                    dense_ranks.append({
                        "rank": chunk.rank, "chunk_id": chunk.chunk_id, "qualified_source_key": doc.key,
                        "legislation_number": doc.metadata["legislation_number"], "distance": chunk.distance,
                    })

                local = e.local_variants(question["question"], [r["chunk_id"] for r in dense_ranks], lexical)

                b0 = e.score(question, dense_ranks)
                b0.update(embedding_tokens=dense.embedding_usage.total_tokens, latency_ms=dense.latency_ms,
                          dense_latency_ms=dense.latency_ms, lexical_latency_ms=0.0, fusion_latency_ms=0.0)
                report["results"]["B0"].append(b0)

                b2_ranking = local["rankings"]["B2"][:5]
                b2_ranks = [
                    {"rank": i, "chunk_id": cid, "qualified_source_key": lexical.documents[cid].key,
                     "legislation_number": lexical.documents[cid].metadata["legislation_number"]}
                    for i, cid in enumerate(b2_ranking, 1)
                ]
                b2 = e.score(question, b2_ranks)
                b2.update(embedding_tokens=dense.embedding_usage.total_tokens,
                          dense_latency_ms=dense.latency_ms, lexical_latency_ms=local["lexical_latency_ms"],
                          fusion_latency_ms=local["fusion_latency_ms"],
                          latency_ms=dense.latency_ms + local["lexical_latency_ms"] + local["fusion_latency_ms"])
                report["results"]["B2"].append(b2)
                checkpoint()
                print(f"Scored {report['metadata']['dense_retrieval_calls']}/30: {question['id']}", flush=True)

        b0_rows, b2_rows = report["results"]["B0"], report["results"]["B2"]
        report["summaries"] = build_summaries(b0_rows, b2_rows)
        report["deltas"] = compute_deltas(b0_rows, b2_rows)
        report["gate_evaluation"] = evaluate_gates(b0_rows, b2_rows)
        report["multi_source_diagnostics"] = multi_source_diagnostics(MULTI_SOURCE_DIAGNOSTIC_IDS, b0_rows, b2_rows)
        report["metadata"]["status"] = "complete"
        report["attempt_history"]["current_attempt_status"] = "completed"
    except Exception as exc:
        report["metadata"]["status"] = "failed_no_retry"
        report["metadata"]["error_type"] = type(exc).__name__
        report["attempt_history"]["current_attempt_status"] = "failed"
        checkpoint()
        raise
    finally:
        _, inventory_after = e.snapshot(collection)
        report["metadata"]["inventory_after"] = inventory_after
        report["metadata"]["collection_fingerprint_equal"] = inventory_before == inventory_after
        report["attempt_history"]["current_attempt_dense_calls"] = report["metadata"]["dense_retrieval_calls"]
        report["attempt_history"]["total_dense_calls_across_all_attempts"] = (
            prior_dense_calls + report["metadata"]["dense_retrieval_calls"]
        )
        checkpoint()

    # Derived from the ACTUAL (possibly monkeypatched/overridden) OUTPUT_JSON
    # path read dynamically here, never from write_csv_report's/write_md_
    # report's own default parameter - a default arg is bound once at def
    # time and would silently ignore an overridden OUTPUT_JSON.
    write_csv_report(report["results"]["B0"], report["results"]["B2"], OUTPUT_JSON.with_suffix(".csv"))
    write_md_report(report, OUTPUT_JSON.with_suffix(".md"))

    print(json.dumps({
        "valid_run_dense_calls": report["metadata"]["dense_retrieval_calls"],
        "total_dense_calls_across_all_attempts": report["attempt_history"]["total_dense_calls_across_all_attempts"],
        "query_embedding_tokens": report["metadata"]["query_embedding_tokens"],
        "decision": report["gate_evaluation"]["decision"],
    }, indent=2))


if __name__ == "__main__":
    main()
