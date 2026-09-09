"""Isolated M10E-A development experiments; never adopt or mutate production.

B0 is frozen M10D. B1 BM25, B2 RRF, B3 source deduplication have fixed
parameters in config. B4 is deliberately skipped: lexical overlap between
complementary provisions does not justify an unvalidated diversity penalty.
M10D source identity is used only for this benchmark, not a future universal
document identity contract (deferred to M11). No holdout is read or created.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import subprocess
import time
import unicodedata
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src import config, evaluate_multilaw as m, retrieve

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "reports/evaluation/m10d-two-law-retrieval.json"
OUTPUT = ROOT / "reports/evaluation/m10e-retrieval-experiments.json"
PRIORITY = ("q002", "q042", "gk004", "gk012", "gk014", "gk019", "gk020", "gk028", "gk022", "gk029")
DEFINITIONS = {
    "B0": "Frozen M10D dense Top-5; no new baseline retrieval.",
    "B1": "BM25 over persisted article_title + section_context + document; positive scores only, Top-20 candidates, Top-5 output.",
    "B2": "Dense Top-20 + BM25 Top-20 RRF; sum 1/(60+rank), missing membership zero; descending score, ascending chunk ID ties.",
    "B3": "Deduplicate the full B2 candidate ranking by M10D QualifiedSourceKey, retaining first, then select Top-5.",
    "B4": "SKIPPED before experiments: shared titles/sections/text can be complementary evidence. No independently justified diversity penalty; no arbitrary tuning.",
}


def tokenize(text: str) -> list[str]:
    """NFC, Turkish I/İ lowercase, Unicode alphanumeric tokens; no stemming."""
    lowered = unicodedata.normalize("NFC", text).translate(str.maketrans({"I": "ı", "İ": "i"})).lower()
    return re.findall(r"[^\W_]+", lowered, flags=re.UNICODE)


@dataclass(frozen=True)
class Document:
    """One persisted corpus record; no question or gold fields."""

    id: str
    text: str
    metadata: dict[str, Any]

    @property
    def key(self) -> str:
        """Return the existing benchmark-specific qualified source identity."""
        return str(m.QualifiedSourceKey.build(self.metadata.get("legislation_number"),
                   self.metadata.get("article_type"), self.metadata.get("article_no")))

    @property
    def lexical_text(self) -> str:
        """Use only permitted persisted fields, with no synthetic law labels."""
        return "\n".join(str(v) for v in (self.metadata.get("article_title"),
                          self.metadata.get("section_context"), self.text) if v)


class BM25:
    """Deterministic Okapi BM25, positive log-IDF and binary query-term weight."""

    def __init__(self, documents: list[Document]) -> None:
        self.documents = {d.id: d for d in documents}
        if not documents or len(self.documents) != len(documents):
            raise ValueError("Corpus must be nonempty with unique IDs")
        self.terms = {d.id: Counter(tokenize(d.lexical_text)) for d in documents}
        self.lengths = {cid: sum(terms.values()) for cid, terms in self.terms.items()}
        self.average_length = sum(self.lengths.values()) / len(documents)
        self.df: Counter[str] = Counter()
        for terms in self.terms.values():
            self.df.update(terms.keys())

    def rank(self, query: str) -> list[tuple[str, float]]:
        """Sum IDF * tf*(k1+1)/(tf+k1*(1-b+b*dl/avgdl)); omit zero scores."""
        scores = []
        n = len(self.documents)
        for cid in sorted(self.documents):
            score = 0.0
            for token in sorted(set(tokenize(query))):
                tf = self.terms[cid][token]
                if tf:
                    idf = math.log(1 + (n - self.df[token] + 0.5) / (self.df[token] + 0.5))
                    norm = config.M10E_BM25_K1 * (1 - config.M10E_BM25_B +
                            config.M10E_BM25_B * self.lengths[cid] / self.average_length)
                    score += idf * tf * (config.M10E_BM25_K1 + 1) / (tf + norm)
            if score > 0:
                scores.append((cid, score))
        return sorted(scores, key=lambda item: (-item[1], item[0]))[:config.M10E_LEXICAL_CANDIDATE_K]


def rrf(dense: list[str], lexical: list[str]) -> list[tuple[str, float]]:
    """Fuse chunk ranks; ties resolve by ascending chunk ID, not input order."""
    scores: dict[str, float] = {}
    for ranking in (dense, lexical):
        if len(set(ranking)) != len(ranking):
            raise ValueError("Duplicate chunk ID in candidate ranking")
        for rank, cid in enumerate(ranking, 1):
            scores[cid] = scores.get(cid, 0.0) + 1 / (config.M10E_RRF_K + rank)
    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))


def deduplicate(ranking: list[str], documents: dict[str, Document]) -> list[str]:
    """Keep the first chunk per qualified source across the full ranking."""
    seen: set[str] = set()
    selected = []
    for cid in ranking:
        key = documents[cid].key
        if key not in seen:
            seen.add(key)
            selected.append(cid)
    return selected


def local_variants(query: str, dense_ids: list[str], lexical: BM25) -> dict[str, Any]:
    """Rank locally using only the original query and cached dense IDs; no gold."""
    start = time.perf_counter()
    lexical_ranking = lexical.rank(query)
    lexical_ms = (time.perf_counter() - start) * 1000
    start = time.perf_counter()
    fused = rrf(dense_ids, [cid for cid, _ in lexical_ranking])
    fusion_ms = (time.perf_counter() - start) * 1000
    start = time.perf_counter()
    unique = deduplicate([cid for cid, _ in fused], lexical.documents)
    dedup_ms = (time.perf_counter() - start) * 1000
    return {"rankings": {"B1": [cid for cid, _ in lexical_ranking],
                         "B2": [cid for cid, _ in fused], "B3": unique},
            "lexical_scores": lexical_ranking, "rrf_scores": fused,
            "lexical_latency_ms": lexical_ms, "fusion_latency_ms": fusion_ms,
            "deduplication_latency_ms": dedup_ms}


def collect_dense(query: str, *, collection: Any, client: Any) -> retrieve.RetrievalResult:
    """Exactly one unchanged production call; no retries, filters, or rewriting."""
    return retrieve.retrieve(query, collection=collection, client=client,
                             model=config.EMBEDDING_MODEL, top_k=config.M10E_DENSE_CANDIDATE_K)


def score(question: dict[str, Any], ranks: list[dict[str, Any]]) -> dict[str, Any]:
    """Apply frozen M10D set matching to an already selected Top-5 ranking."""
    ranks = ranks[:5]
    expected = set(question["expected_sources"])
    laws = set(question["expected_legislations"])
    keys = [r["qualified_source_key"] for r in ranks]
    result = {k: question[k] for k in ("id", "question", "dataset", "expected_sources",
                                      "expected_legislations", "case_type", "difficulty")}
    result.update(ranks=ranks, top1_legislation=ranks[0]["legislation_number"] if ranks else None,
                  expected_source_ranks={key: keys.index(key) + 1 if key in keys else None for key in sorted(expected)})
    for k in (1, 3, 5):
        result[f"any_source_hit_at_{k}"] = bool(expected.intersection(keys[:k]))
        result[f"all_sources_match_at_{k}"] = expected.issubset(keys[:k])
        result[f"expected_legislation_hit_at_{k}"] = any(r["legislation_number"] in laws for r in ranks[:k])
    known = [r for r in ranks if r["legislation_number"] is not None]
    count = sum(r["legislation_number"] not in laws for r in known)
    result.update(non_expected_legislation_count_at_5=count,
                  non_expected_legislation_share_at_5=count / len(known) if known else None)
    return result


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize the same denominators as M10D plus measured component timings."""
    if not rows:
        raise ValueError("Cannot summarize an empty group")
    result: dict[str, Any] = {"total_questions": len(rows)}
    for metric, field in (("any_qualified_recall", "any_source_hit"),
                          ("all_qualified_match", "all_sources_match"),
                          ("legislation_hit", "expected_legislation_hit")):
        for k in (1, 3, 5):
            result[f"{metric}_at_{k}"] = sum(r[f"{field}_at_{k}"] for r in rows) / len(rows)
    known = [r for r in rows if r["top1_legislation"] is not None]
    unexpected = sum(r["top1_legislation"] not in r["expected_legislations"] for r in known)
    shares = [r["non_expected_legislation_share_at_5"] for r in rows if r["non_expected_legislation_share_at_5"] is not None]
    result.update(top1_unexpected_legislation_count=unexpected,
                  top1_unexpected_legislation_rate=unexpected / len(known) if known else None,
                  average_non_expected_legislation_share_at_5=sum(shares) / len(shares) if shares else None)
    for field in ("latency_ms", "dense_latency_ms", "lexical_latency_ms", "fusion_latency_ms", "deduplication_latency_ms"):
        values = [r[field] for r in rows if r.get(field) is not None]
        result["average_" + field] = sum(values) / len(values) if values else None
    tokens = [r.get("embedding_tokens") for r in rows]
    result["query_embedding_tokens"] = sum(tokens) if all(t is not None for t in tokens) else None
    return result


def breakdown(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize law subsets, 4458 categories/difficulty and single-source cases."""
    customs = [r for r in rows if r["dataset"] == "4458"]
    result = {law: summarize([r for r in rows if r["dataset"] == law]) for law in ("5326", "4458")}
    result["combined"] = summarize(rows)
    for field in ("case_type", "difficulty"):
        result[field + "_4458"] = {v: summarize([r for r in customs if r[field] == v])
                                    for v in sorted({r[field] for r in customs})}
    result["single_source_4458"] = summarize([r for r in customs if len(r["expected_sources"]) == 1])
    return result


def snapshot(collection: Any) -> tuple[list[Document], dict[str, Any]]:
    """Read only IDs/documents/metadata; fingerprint every persisted text/metadata field."""
    payload = collection.get(include=["documents", "metadatas"])
    if not len(payload["ids"]) == len(payload["documents"]) == len(payload["metadatas"]):
        raise ValueError("Misaligned corpus payload")
    documents = sorted((Document(cid, text, meta) for cid, text, meta in
                        zip(payload["ids"], payload["documents"], payload["metadatas"])), key=lambda d: d.id)
    if len({d.id for d in documents}) != len(documents):
        raise ValueError("Duplicate corpus ID")
    for d in documents:
        if not isinstance(d.text, str):
            raise ValueError("Missing corpus text")
        _ = d.key
    rows = [(d.id, d.text, d.metadata) for d in documents]
    digest = hashlib.sha256(json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    inventory = {"total": collection.count(), "counts": dict(Counter(d.metadata["legislation_number"] for d in documents)),
                 "ids": [d.id for d in documents], "content_sha256": digest,
                 "fingerprint_scope": "Sorted IDs, full documents and all metadata; no raw embeddings requested."}
    if inventory["total"] != 329 or len(documents) != 329 or inventory["counts"] != {"5326": 53, "4458": 276}:
        raise ValueError("Production inventory differs from frozen M10D")
    return documents, inventory


def file_hashes(paths: list[Path]) -> dict[str, str]:
    """Hash files without modifying them or exposing their contents."""
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def frozen_inputs() -> tuple[dict[str, Any], dict[str, str]]:
    """Validate current datasets and exact question/target equality to frozen B0."""
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    questions = m.load_combined_benchmark()
    if len(questions) != 75 or len(baseline["results"]) != 75:
        raise ValueError("Expected exactly 75 frozen questions")
    for q, row in zip(questions, baseline["results"]):
        if (q.id, q.question, sorted(map(str, q.expected_sources))) != (row["id"], row["question"], sorted(row["expected_sources"])):
            raise ValueError("Frozen question identity/text/gold mismatch")
    paths = [m.SEED_5326_PATH, m.EXTENSION_5326_PATH, m.QUESTIONS_4458_PATH, m.M9B_PROVISIONAL_PATH]
    for name, path in zip(("seed_5326", "extension_5326", "frozen_4458", "m9b_provisional"), paths):
        if hashlib.sha256(path.read_bytes()).hexdigest() != baseline["metadata"]["dataset_sha256"][name]:
            raise ValueError("Frozen dataset hash mismatch: " + name)
    paths += [BASELINE, BASELINE.with_suffix(".csv"), ROOT / "evaluation/questions_4458.candidate.json"]
    return baseline, file_hashes(paths)


def prefix_comparison(baseline: list[dict[str, Any]], dense: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare ordered chunk IDs and qualified keys independently; distances excluded."""
    ids_equal = [r["chunk_id"] for r in baseline[:5]] == [r["chunk_id"] for r in dense[:5]]
    keys_equal = [r["qualified_source_key"] for r in baseline[:5]] == [r["qualified_source_key"] for r in dense[:5]]
    return {"exact_chunk_id_ranking_match": ids_equal, "qualified_key_sequence_match": keys_equal,
            "frozen_top5": baseline[:5], "new_dense_top5": dense[:5]}


def recommend(summaries: dict[str, Any]) -> dict[str, Any]:
    """Apply predeclared conservative gates, using exact rates rather than rounded thresholds."""
    base = summaries["B0"]
    assessments = {}
    for strategy in ("B1", "B2", "B3"):
        s = summaries[strategy]
        gates = {
            "5326_preserved": all(s["5326"][metric] >= base["5326"][metric] for metric in
                                  ("any_qualified_recall_at_5", "all_qualified_match_at_5")),
            "4458_both_top5_improve": all(s["4458"][metric] > base["4458"][metric] for metric in
                                         ("any_qualified_recall_at_5", "all_qualified_match_at_5")),
            "top1_law_no_degradation": s["combined"]["legislation_hit_at_1"] >= base["combined"]["legislation_hit_at_1"],
            "multi_part_all5_improves": s["case_type_4458"]["multi_part"]["all_qualified_match_at_5"] > base["case_type_4458"]["multi_part"]["all_qualified_match_at_5"],
            "single_source_preserved": s["single_source_4458"]["any_qualified_recall_at_5"] >= base["single_source_4458"]["any_qualified_recall_at_5"],
            "deterministic_low_cost": True,
        }
        assessments[strategy] = {"criteria": gates, "eligible": all(gates.values())}
    eligible = [s for s in assessments if assessments[s]["eligible"]]
    selected = max(eligible, key=lambda s: (summaries[s]["4458"]["all_qualified_match_at_5"],
                    summaries[s]["4458"]["any_qualified_recall_at_5"], -int(s[1:]))) if eligible else None
    return {"recommended_candidate": selected, "assessments": assessments,
            "reason": "Candidate passes all predeclared gates; prioritize 4458 completeness, then recall, then simplicity." if selected else
                      "No experimental strategy satisfies every preservation/improvement gate; retain production unchanged.",
            "scope": "Development-benchmark evidence only. M10E-B blind holdout required before M10F production adoption."}


def write_csv(report: dict[str, Any], path: Path) -> None:
    """Export per-question metrics and rankings, with no corpus text or embeddings."""
    rows = [dict(strategy=s, **r) for s, results in report["results"].items() for r in results]
    with path.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v for k, v in row.items()})


def main() -> None:
    """Run once after the offline gate; checkpoint each call and refuse existing output."""
    if not config.OPENAI_API_KEY or os.getenv("RUN_OPENAI_INTEGRATION_TESTS") != "1":
        raise RuntimeError("Requires OPENAI_API_KEY and RUN_OPENAI_INTEGRATION_TESTS=1")
    if OUTPUT.exists() or OUTPUT.with_suffix(".csv").exists():
        raise RuntimeError("Experiment output exists; refusing a second real run")
    baseline, hashes = frozen_inputs()
    if config.COLLECTION_NAME != baseline["metadata"]["collection_name"] or config.EMBEDDING_MODEL != baseline["metadata"]["embedding_model"]:
        raise ValueError("Configured collection/model differs from frozen M10D")
    from src import index
    from openai import OpenAI

    storage = sorted(p for p in Path(config.CHROMA_PATH).resolve().rglob("*") if p.is_file())
    storage_before = file_hashes(storage)
    collection = index.get_client().get_collection(name=config.COLLECTION_NAME, embedding_function=None)
    documents, inventory = snapshot(collection)
    if retrieve.distance_metric(collection) != baseline["metadata"]["distance_metric"]:
        raise ValueError("Distance metric changed")
    start = time.perf_counter()
    lexical = BM25(documents)
    build_ms = (time.perf_counter() - start) * 1000
    report: dict[str, Any] = {
        "metadata": {"timestamp": datetime.now(timezone.utc).isoformat(), "status": "collecting",
                     "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                     "collection_name": config.COLLECTION_NAME, "embedding_model": config.EMBEDDING_MODEL,
                     "distance_metric": retrieve.distance_metric(collection), "sdk_max_retries": 0,
                     "development_only": True, "lexical_index_build_latency_ms": build_ms},
        "strategy_definitions": DEFINITIONS,
        "fixed_parameters": {"dense_candidate_k": config.M10E_DENSE_CANDIDATE_K,
                             "lexical_candidate_k": config.M10E_LEXICAL_CANDIDATE_K,
                             "bm25_k1": config.M10E_BM25_K1, "bm25_b": config.M10E_BM25_B,
                             "rrf_k": config.M10E_RRF_K, "top_k": 5,
                             "bm25_idf": "ln(1+(N-df+0.5)/(df+0.5))", "query_tf": "binary",
                             "tokenizer": "NFC; I->ı, İ->i; Unicode lowercase; Unicode alphanumeric tokens; no stemming/stopwords",
                             "tie_break": "ascending chunk ID", "zero_bm25_scores": "excluded",
                             "acceptance": "Exact B0 rates; no Top-1 law degradation; both 4458 Top-5 rates and multi_part ALL@5 strictly improve; single-source preserved"},
        "frozen_baseline": {"path": str(BASELINE.relative_to(ROOT)), "metadata": baseline["metadata"],
                            **{k: baseline[k] for k in ("summary_5326", "summary_4458", "summary_combined")}},
        "frozen_file_hashes_before": hashes, "inventory_before": inventory,
        "storage_file_hashes_before": storage_before,
        "dense_calls_attempted": 0, "dense_calls_completed": 0, "query_embedding_tokens": 0,
        "bm25_openai_calls": 0, "generation_calls": 0, "candidate_cache": {}, "prefix_comparisons": {},
        "results": {"B0": [], "B1": [], "B2": [], "B3": []},
        "latency_accounting": "B0 historical; B1 lexical only; B2 dense+lexical+fusion; B3 adds dedup. Shared dense time/tokens attributed per strategy, never summed across variants. Index build and report I/O excluded.",
    }
    # Exclusive create precedes the first network operation, so interruption cannot
    # silently cause a fresh paid run. Checkpoints contain no texts or vectors.
    with OUTPUT.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)

    def checkpoint() -> None:
        OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    try:
        with OpenAI(api_key=config.OPENAI_API_KEY, max_retries=0) as client:
            for question in baseline["results"]:
                qid = question["id"]
                report["dense_calls_attempted"] += 1
                report["metadata"]["active_question"] = qid
                checkpoint()
                dense = collect_dense(question["question"], collection=collection, client=client)
                report["dense_calls_completed"] += 1
                dense_ranks = []
                for chunk in dense.results:
                    doc = lexical.documents[chunk.chunk_id]
                    if chunk.text != doc.text or chunk.metadata != doc.metadata:
                        raise ValueError("Dense record differs from inventory snapshot")
                    dense_ranks.append({"rank": chunk.rank, "chunk_id": chunk.chunk_id,
                                        "qualified_source_key": doc.key, "legislation_number": doc.metadata["legislation_number"],
                                        "distance": chunk.distance})
                report["candidate_cache"][qid] = {"dense_top20": dense_ranks, "embedding_tokens": dense.embedding_usage.total_tokens,
                                                 "dense_latency_ms": dense.latency_ms}
                checkpoint()
                if len(dense_ranks) != 20 or dense.embedding_usage.total_tokens is None:
                    raise ValueError("Incomplete dense payload/usage; stop without retries")
                report["query_embedding_tokens"] += dense.embedding_usage.total_tokens
                report["prefix_comparisons"][qid] = prefix_comparison(question["ranks"], dense_ranks)
                local = local_variants(question["question"], [r["chunk_id"] for r in dense_ranks], lexical)
                report["candidate_cache"][qid].update(local)
                b0 = score(question, question["ranks"])
                for key, value in b0.items():
                    if key in question and key not in ("ranks",) and question[key] != value:
                        raise ValueError("M10D scoring parity failure: " + key)
                b0.update(latency_ms=question["retrieval_latency_ms"], dense_latency_ms=question["retrieval_latency_ms"],
                          lexical_latency_ms=0.0, fusion_latency_ms=0.0, deduplication_latency_ms=0.0,
                          embedding_tokens=question["embedding_tokens"])
                report["results"]["B0"].append(b0)
                for strategy, ranking in local["rankings"].items():
                    ranks = [{"rank": i, "chunk_id": cid, "qualified_source_key": lexical.documents[cid].key,
                              "legislation_number": lexical.documents[cid].metadata["legislation_number"]}
                             for i, cid in enumerate(ranking[:5], 1)]
                    row = score(question, ranks)
                    dense_ms = dense.latency_ms if strategy != "B1" else 0.0
                    fusion_ms = local["fusion_latency_ms"] if strategy != "B1" else 0.0
                    dedup_ms = local["deduplication_latency_ms"] if strategy == "B3" else 0.0
                    row.update(dense_latency_ms=dense_ms, lexical_latency_ms=local["lexical_latency_ms"],
                               fusion_latency_ms=fusion_ms, deduplication_latency_ms=dedup_ms,
                               latency_ms=dense_ms + local["lexical_latency_ms"] + fusion_ms + dedup_ms,
                               embedding_tokens=dense.embedding_usage.total_tokens if strategy != "B1" else 0)
                    report["results"][strategy].append(row)
                checkpoint()
                print(f"Collected {report['dense_calls_completed']}/75: {qid}", flush=True)
        report["summaries"] = {s: breakdown(rows) for s, rows in report["results"].items()}
        report["recommendation"] = recommend(report["summaries"])
        report["priority_cases"] = {qid: {s: next(r for r in rows if r["id"] == qid)
                                       for s, rows in report["results"].items()} for qid in PRIORITY}
        comparisons = report["prefix_comparisons"]
        report["dense_prefix_integrity"] = {
            "exact_ranking_match_count": sum(v["exact_chunk_id_ranking_match"] for v in comparisons.values()),
            "same_qualified_key_sequence_count": sum(v["qualified_key_sequence_match"] for v in comparisons.values()),
            "different_question_ids": [qid for qid, v in comparisons.items() if not v["exact_chunk_id_ranking_match"]],
            "definition": "Exact ranking means ordered chunk IDs, not floating-point distance equality. B0 remains frozen."}
        report["metadata"]["status"] = "complete"
    except Exception as exc:
        report["metadata"]["status"] = "failed_no_retry"
        report["metadata"]["error_type"] = type(exc).__name__
        raise
    finally:
        _, report["inventory_after"] = snapshot(collection)
        report["collection_fingerprint_equal"] = inventory == report["inventory_after"]
        report["frozen_file_hashes_after"] = file_hashes([ROOT / p for p in hashes])
        report["storage_file_hashes_after"] = file_hashes(sorted(p for p in Path(config.CHROMA_PATH).resolve().rglob("*") if p.is_file()))
        report["storage_fingerprint_equal"] = storage_before == report["storage_file_hashes_after"]
        immutable = (report["collection_fingerprint_equal"] and hashes == report["frozen_file_hashes_after"]
                     and report["storage_fingerprint_equal"])
        if not immutable:
            report["metadata"]["status"] = "integrity_failed"
        checkpoint()
        if report["dense_calls_completed"] == 75 and all(len(rows) == 75 for rows in report["results"].values()):
            write_csv(report, OUTPUT.with_suffix(".csv"))
        if not immutable:
            raise RuntimeError("Immutability verification failed; inspect saved report, do not rerun")
    print(json.dumps({"calls": report["dense_calls_completed"], "tokens": report["query_embedding_tokens"],
                      "prefix": report["dense_prefix_integrity"], "recommendation": report["recommendation"]}, indent=2))


if __name__ == "__main__":
    main()
