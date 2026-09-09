"""
Two-law retrieval evaluation (Milestone M10D).

Scope: measure retrieval behavior against the REAL shared two-law Chroma
collection (5326 + 4458, 329 records total, see docs/indexing.md / M10C).
THIS MODULE IS RETRIEVAL-ONLY: it never calls an LLM, never generates an
answer (`src/generate.py`/`src/rag.py` are unreferenced), and never tunes
`TOP_K`, the distance metric, the embedding model/text, or query wording in
response to a measured score. It reuses `src.retrieve.retrieve()` - the real
production retrieval path - exactly once per question; it does not
implement a second, competing retrieval/indexing/embedding pipeline.

Why article_no alone is insufficient (see docs/evaluation.md): in a
single-law corpus, "27" unambiguously means one Article. In the shared
two-law corpus this is no longer true - 5326 Madde 27 and 4458 Madde 27 are
different sources, and even within 4458 alone, the main-law Geçici Madde 1
and the "4458 SAYILI KANUNA İŞLENEMEYEN HÜKÜMLER" section's own Geçici
Madde 1 share `legislation_number` + `article_no` but are structurally
distinct (`article_type` differs: "gecici" vs "islenemeyen_hukum"). This
module therefore matches ground truth against retrieved results using the
`QualifiedSourceKey` triple (`legislation_number`, `article_type`,
normalized `article_no`) everywhere except the frozen historical 5326
regression baseline (see `historical_5326_question_outcomes` - old
article-number-only matching is preserved there, and proven equivalent to
qualified matching for that frozen set - see module docstring §"5326
adapter" below and docs/evaluation.md).

5326 adapter (§5): the frozen `tests/questions.json` +
`evaluation/questions_m9b.json` (q001-q045) predate the two-law corpus and
store only bare `expected_articles`, with no `legislation_number`/
`article_type` field. Those files are NEVER modified here. Instead,
`load_5326_questions()` wraps each frozen question's `expected_articles`
into `QualifiedSourceKey("5326", "normal", article_no)` - every one of the
45 frozen questions was verified (during M10D construction) to target a
`normal`-type 5326 Article, and qualified matching was proven to produce
IDENTICAL Hit@K/ALL-match@K results to the old article-number-only matching
for all 45 questions (including the two whose expected number, "2"/"3",
collides with a real `ek`/`gecici` 5326 Article of the same number) by
computing both against the frozen `reports/evaluation/m9b-provisional.json`
per-question results.

Historical PRE-expansion source (§23B): the pre-4458 per-question 5326
outcomes come ONLY from the frozen `reports/evaluation/m9b-provisional.json`
artifact (never a re-run of the old 53-record collection, never inferred
from aggregate percentages). Its `retrieved_articles` field stores only raw
article_no per rank (ambiguous for the 5326 corpus's 1 `ek` + 3 `gecici`
Articles that share a number with a `normal` Article), so
`historical_5326_question_outcomes()` resolves each rank's true
`article_type` via `retrieved_chunk_ids` joined against the real, unchanged
`data/processed/5326-kabahatler-kanunu.chunks.json` Chunk records (a lookup
against trusted persisted metadata - not string-parsing or inferring from
prose).

4458 dataset (§6-§14): `evaluation/questions_4458.json` is the FROZEN,
human-gold-approved 30-question benchmark (`evaluation/questions_4458.
candidate.json` is its pre-approval historical predecessor and is never
read by this module's real-run path). `load_4458_questions()` strictly
validates the frozen file's schema before any retrieval call.

Legislation Hit@K (§21) vs Qualified Recall@K: Legislation Hit@K answers
"did retrieval enter the correct law", Qualified Recall@K answers "did
retrieval find the exact correct source". Cross-law intrusion diagnostics
(§22) are explicitly documented as NOT a legal-error metric (a result from
the other law can still be legally relevant) - see `_pct` usages in the
CLI and docs/evaluation.md.

Cross-law multi-source questions (5326 + 4458 evidence required together)
are explicitly OUT OF SCOPE for M10D (§12) and deferred to a later
dedicated interaction benchmark.

Collection safety: this module's real-run path (`main`) only ever opens the
existing production collection (`collection.get`/`collection.query` via
`src.retrieve`, opened with `client.get_collection`) - it never calls
`upsert`/`add`/`delete`, never rebuilds/recreates the collection, and
verifies the collection's total/per-law counts are unchanged before and
after the run.

CLI usage (manual/local validation only - not part of the automated test
suite; requires BOTH `OPENAI_API_KEY` and `RUN_OPENAI_INTEGRATION_TESTS=1`,
mirroring every other real-API gate in this project):
    RUN_OPENAI_INTEGRATION_TESTS=1 python -m src.evaluate_multilaw
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from chromadb.api.models.Collection import Collection

from src import config, evaluate, evaluation_dataset, retrieve

if __name__ == "__main__":  # pragma: no cover - exercised via CLI, not tests
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
QUESTIONS_4458_PATH = PROJECT_ROOT / "evaluation" / "questions_4458.json"
QUESTIONS_4458_CANDIDATE_PATH = PROJECT_ROOT / "evaluation" / "questions_4458.candidate.json"
SEED_5326_PATH = evaluate.DEFAULT_QUESTIONS_PATH
EXTENSION_5326_PATH = evaluation_dataset.M9B_EXTENSION_PATH
M9B_PROVISIONAL_PATH = PROJECT_ROOT / "reports" / "evaluation" / "m9b-provisional.json"
CHUNKS_5326_PATH = PROJECT_ROOT / "data" / "processed" / "5326-kabahatler-kanunu.chunks.json"
PARAGRAPHS_4458_PATH = PROJECT_ROOT / "data" / "processed" / "4458-gumruk-kanunu.paragraphs.json"
JSON_REPORT_PATH = PROJECT_ROOT / "reports" / "evaluation" / "m10d-two-law-retrieval.json"
CSV_REPORT_PATH = PROJECT_ROOT / "reports" / "evaluation" / "m10d-two-law-retrieval.csv"

# Production-configured depth; Top-1/3/5 are sliced from one ranked result.
EVAL_TOP_K = config.TOP_K

ALLOWED_CASE_TYPES = evaluation_dataset.ALLOWED_CASE_TYPES
ALLOWED_DIFFICULTIES = evaluation_dataset.ALLOWED_DIFFICULTIES
ALLOWED_ARTICLE_TYPES = frozenset({"normal", "ek", "gecici", "islenemeyen_hukum"})
EXPECTED_4458_IDS = tuple(f"gk{n:03d}" for n in range(1, 31))


class MultiLawEvaluationError(RuntimeError):
    """Raised for malformed 4458 dataset input, a combined-benchmark ID
    collision, or a QualifiedSourceKey with missing/invalid components.
    Never silently evaluates malformed ground truth (mirrors
    `evaluate.EvaluationError`).
    """


# ============================================================================
# QualifiedSourceKey (§4)
# ============================================================================


@dataclass(frozen=True, order=True)
class QualifiedSourceKey:
    """(legislation_number, article_type, normalized article_no) - the
    canonical M10D ground-truth/retrieved-source identity. `article_no` is
    always normalized via `evaluate.normalize_article_no` (reused, not
    reimplemented) so e.g. "42/A" and "42-a" compare equal, while distinct
    legislation_number or article_type values are NEVER conflated - unlike
    the legacy single-law article_no-only matching this replaces for the
    two-law corpus.
    """

    legislation_number: str
    article_type: str
    article_no: str

    @staticmethod
    def build(legislation_number: Any, article_type: Any, article_no: Any) -> "QualifiedSourceKey":
        """Validate metadata and normalize only the article-number component."""
        if not isinstance(legislation_number, str) or not legislation_number.strip():
            raise MultiLawEvaluationError(f"legislation_number must be a non-empty str, got {legislation_number!r}")
        if not isinstance(article_type, str) or article_type not in ALLOWED_ARTICLE_TYPES:
            raise MultiLawEvaluationError(f"article_type must be one of {sorted(ALLOWED_ARTICLE_TYPES)}, got {article_type!r}")
        if not isinstance(article_no, str) or not article_no.strip():
            raise MultiLawEvaluationError("article_no must be a non-empty str")
        return QualifiedSourceKey(
            legislation_number=legislation_number,
            article_type=article_type,
            article_no=evaluate.normalize_article_no(article_no),
        )

    def __str__(self) -> str:
        return f"{self.legislation_number}/{self.article_type}/{self.article_no}"


# ============================================================================
# Question loading
# ============================================================================


@dataclass(frozen=True)
class MultiLawQuestion:
    """One question in the combined 75-question M10D benchmark."""

    id: str
    question: str
    dataset: str  # "5326" | "4458"
    expected_sources: frozenset[QualifiedSourceKey]
    expected_legislations: frozenset[str]
    case_type: str | None = None
    difficulty: str | None = None


def load_5326_questions() -> list[MultiLawQuestion]:
    """Load the frozen 45-question 5326 benchmark (q001-q045, seed +
    extension) via the EXISTING `evaluation_dataset.load_m9b_benchmark()`
    loader - `tests/questions.json`/`evaluation/questions_m9b.json` are
    read-only here, never modified. Applies the §5 adapter: every
    `expected_articles` entry is wrapped as
    `QualifiedSourceKey("5326", "normal", article_no)` - see module
    docstring for the proof this is equivalent to legacy matching for this
    frozen set.
    """
    base_questions = evaluation_dataset.load_m9b_benchmark()
    result: list[MultiLawQuestion] = []
    for q in base_questions:
        sources = frozenset(QualifiedSourceKey.build("5326", "normal", a) for a in q.expected_articles)
        result.append(
            MultiLawQuestion(
                id=q.id,
                question=q.question,
                dataset="5326",
                expected_sources=sources,
                expected_legislations=frozenset({"5326"}),
                case_type=getattr(q, "case_type", None),
                difficulty=getattr(q, "difficulty", None),
            )
        )
    return result


def _real_4458_qualified_keys() -> frozenset[QualifiedSourceKey]:
    """Every QualifiedSourceKey that actually exists in the current 4458
    corpus, derived by reusing the EXISTING `src.chunk.parse_articles()`
    parser (never a competing parser). Returns an empty frozenset (skipping
    the §13 existence check) if the local ignored raw paragraphs artifact is
    absent, matching this project's established `data/raw/`-dependent skip
    pattern (see tests/test_chunk_4458.py).
    """
    if not PARAGRAPHS_4458_PATH.exists():
        return frozenset()
    from src import chunk as chunk_module

    _, articles = chunk_module._load_and_parse_articles(PARAGRAPHS_4458_PATH)
    return frozenset(QualifiedSourceKey.build(a.legislation_number, a.article_type, a.article_no) for a in articles)


def _validate_4458_raw_question(raw: Any, *, expected_id: str) -> None:
    if not isinstance(raw, dict):
        raise MultiLawEvaluationError(f"Question for {expected_id} must be a JSON object")
    if raw.get("id") != expected_id:
        raise MultiLawEvaluationError(f"4458 dataset IDs must be gk001..gk030 in order; expected {expected_id!r}, got {raw.get('id')!r}")
    question_text = raw.get("question")
    if not isinstance(question_text, str) or not question_text.strip():
        raise MultiLawEvaluationError(f"{expected_id}: missing/empty 'question'")
    if raw.get("case_type") not in ALLOWED_CASE_TYPES:
        raise MultiLawEvaluationError(f"{expected_id}: invalid case_type {raw.get('case_type')!r}")
    if raw.get("difficulty") not in ALLOWED_DIFFICULTIES:
        raise MultiLawEvaluationError(f"{expected_id}: invalid difficulty {raw.get('difficulty')!r}")
    if raw.get("source_verified") is not True:
        raise MultiLawEvaluationError(f"{expected_id}: source_verified must be true")
    if raw.get("expert_validated") is not False:
        raise MultiLawEvaluationError(f"{expected_id}: expert_validated must remain false")
    notes = raw.get("notes")
    if not isinstance(notes, str) or not notes.strip():
        raise MultiLawEvaluationError(f"{expected_id}: missing/empty notes")
    sources = raw.get("expected_sources")
    if not isinstance(sources, list) or not sources:
        raise MultiLawEvaluationError(f"{expected_id}: missing/empty expected_sources")


def load_4458_questions(path: str | Path = QUESTIONS_4458_PATH) -> list[MultiLawQuestion]:
    """Load and strictly validate the FROZEN 30-question 4458 dataset
    (§13). Raises `MultiLawEvaluationError` on any structural violation:
    wrong count, wrong ID sequence, invalid case_type/difficulty,
    source_verified != true, expert_validated != false, empty notes, empty/
    non-4458 expected_sources, a duplicate QualifiedSourceKey within one
    question, or a duplicate normalized question text. Does not by itself
    check QualifiedSourceKeys against the parsed corpus - see
    `validate_4458_sources_against_corpus`.
    """
    raw_questions = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw_questions, list):
        raise MultiLawEvaluationError(f"Expected a JSON list of questions in {path}")
    if len(raw_questions) != 30:
        raise MultiLawEvaluationError(f"4458 dataset must contain exactly 30 questions, got {len(raw_questions)}")

    questions: list[MultiLawQuestion] = []
    normalized_texts: set[str] = set()
    for index, raw in enumerate(raw_questions):
        expected_id = EXPECTED_4458_IDS[index]
        _validate_4458_raw_question(raw, expected_id=expected_id)

        seen_in_question: set[QualifiedSourceKey] = set()
        keys: list[QualifiedSourceKey] = []
        for source in raw["expected_sources"]:
            if not isinstance(source, dict):
                raise MultiLawEvaluationError(f"{expected_id}: expected_sources entries must be objects")
            leg = source.get("legislation_number")
            if leg != "4458":
                raise MultiLawEvaluationError(f"{expected_id}: expected_source legislation_number must be '4458', got {leg!r}")
            key = QualifiedSourceKey.build(leg, source.get("article_type"), source.get("article_no"))
            if key in seen_in_question:
                raise MultiLawEvaluationError(f"{expected_id}: duplicate QualifiedSourceKey within one question: {key}")
            seen_in_question.add(key)
            keys.append(key)

        normalized_text = evaluation_dataset.normalize_question_text(raw["question"])
        if normalized_text in normalized_texts:
            raise MultiLawEvaluationError(f"{expected_id}: duplicate normalized question text")
        normalized_texts.add(normalized_text)

        questions.append(
            MultiLawQuestion(
                id=expected_id,
                question=raw["question"],
                dataset="4458",
                expected_sources=frozenset(keys),
                expected_legislations=frozenset({"4458"}),
                case_type=raw["case_type"],
                difficulty=raw["difficulty"],
            )
        )

    distinct_keys = {key for q in questions for key in q.expected_sources}
    if len(distinct_keys) < 20:
        raise MultiLawEvaluationError(f"4458 dataset must cover at least 20 distinct QualifiedSourceKeys, got {len(distinct_keys)}")

    return questions


def validate_4458_sources_against_corpus(questions: list[MultiLawQuestion]) -> None:
    """Verify every expected QualifiedSourceKey in `questions` exists in the
    actual parsed 4458 corpus (§13). No-ops (does not raise) if the local
    ignored raw paragraphs artifact is absent - see `_real_4458_qualified_keys`.
    """
    real_keys = _real_4458_qualified_keys()
    if not real_keys:
        return
    for q in questions:
        for key in q.expected_sources:
            if key not in real_keys:
                raise MultiLawEvaluationError(f"{q.id}: QualifiedSourceKey {key} not found in the parsed 4458 corpus")


def load_combined_benchmark() -> list[MultiLawQuestion]:
    """45 frozen 5326 + 30 frozen approved 4458 = 75 questions, in that
    order. Rejects duplicate IDs across the two datasets (defensive; the
    namespaces q0xx/gkxxx never legitimately collide).
    """
    combined = load_5326_questions() + load_4458_questions()
    ids = [q.id for q in combined]
    if len(set(ids)) != len(ids):
        raise MultiLawEvaluationError("duplicate question IDs across the combined 5326+4458 benchmark")
    return combined


# ============================================================================
# Retrieval -> per-question result (§19-§22)
# ============================================================================


@dataclass(frozen=True)
class RetrievedRankInfo:
    """One ranked Chroma result's identity for M10D matching purposes.
    Missing or invalid source metadata raises MultiLawEvaluationError
    during extraction; identity is never guessed from chunk_id or prose.
    """

    rank: int
    chunk_id: str
    legislation_number: str | None
    article_type: str | None
    article_no: str | None
    qualified_source_key: QualifiedSourceKey
    distance: float


@dataclass(frozen=True)
class QuestionResult:
    """One question's full M10D evaluation outcome (§19)."""

    id: str
    question: str
    dataset: str
    expected_sources: tuple[str, ...]
    expected_legislations: tuple[str, ...]
    case_type: str | None
    difficulty: str | None
    ranks: tuple[RetrievedRankInfo, ...]
    any_source_hit_at_1: bool
    any_source_hit_at_3: bool
    any_source_hit_at_5: bool
    all_sources_match_at_1: bool
    all_sources_match_at_3: bool
    all_sources_match_at_5: bool
    first_expected_source_rank: int | None
    expected_legislation_hit_at_1: bool
    expected_legislation_hit_at_3: bool
    expected_legislation_hit_at_5: bool
    top1_legislation: str | None
    non_expected_legislation_count_at_5: int
    non_expected_legislation_share_at_5: float | None
    embedding_tokens: int | None
    retrieval_latency_ms: float | None
    error_type: str | None
    safe_error: str | None


def _extract_rank_info(results: list[retrieve.RetrievedChunk]) -> list[RetrievedRankInfo]:
    """Build `RetrievedRankInfo` directly from trusted Chroma metadata
    (`legislation_number`/`article_type`/`article_no`) - never inferred from
    `chunk_id` or prose (§4).
    """
    infos = []
    for chunk in results:
        leg = chunk.metadata.get("legislation_number")
        atype = chunk.metadata.get("article_type")
        ano = chunk.metadata.get("article_no")
        qsk = QualifiedSourceKey.build(leg, atype, ano)
        infos.append(
            RetrievedRankInfo(
                rank=chunk.rank, chunk_id=chunk.chunk_id, legislation_number=leg,
                article_type=atype, article_no=ano, qualified_source_key=qsk, distance=chunk.distance,
            )
        )
    return infos


def _any_hit(expected: frozenset[QualifiedSourceKey], ranks: list[RetrievedRankInfo], k: int) -> bool:
    return any(r.qualified_source_key in expected for r in ranks[:k] if r.qualified_source_key is not None)


def _all_match(expected: frozenset[QualifiedSourceKey], ranks: list[RetrievedRankInfo], k: int) -> bool:
    """SET comparison (§20): every expected QualifiedSourceKey must appear
    somewhere in Top-K. NEVER derived from `first_expected_source_rank` -
    for a multi-source question that would silently ignore whether the
    OTHER expected sources were retrieved at all.
    """
    top_k_keys = {r.qualified_source_key for r in ranks[:k] if r.qualified_source_key is not None}
    return expected.issubset(top_k_keys)


def _first_expected_source_rank(expected: frozenset[QualifiedSourceKey], ranks: list[RetrievedRankInfo]) -> int | None:
    for r in ranks:
        if r.qualified_source_key in expected:
            return r.rank
    return None


def _legislation_hit(expected_legislations: frozenset[str], ranks: list[RetrievedRankInfo], k: int) -> bool:
    return any(r.legislation_number in expected_legislations for r in ranks[:k] if r.legislation_number is not None)


def _non_expected_legislation_stats(
    expected_legislations: frozenset[str], ranks: list[RetrievedRankInfo], k: int = 5
) -> tuple[int, float | None]:
    """Cross-law intrusion diagnostic (§22) - NOT a legal-error metric; a
    result from the other law can still be legally relevant. `share` is
    `None` (never 0) when no Top-K result has usable legislation_number
    metadata at all.
    """
    top_k = [r for r in ranks[:k] if r.legislation_number is not None]
    if not top_k:
        return 0, None
    count = sum(1 for r in top_k if r.legislation_number not in expected_legislations)
    return count, count / len(top_k)


def evaluate_question(
    question: MultiLawQuestion,
    *,
    collection: Collection,
    client: Any = None,
    model: str = config.EMBEDDING_MODEL,
    top_k: int = EVAL_TOP_K,
) -> QuestionResult:
    """Call the REAL production retrieval path (`retrieve.retrieve`) EXACTLY
    ONCE for this question (§16) - no retries, no query rewriting, no `where`
    metadata filtering by expected legislation (the entire point of M10D is
    testing unfiltered two-law discrimination).
    """
    expected = question.expected_sources
    if top_k < 5:
        raise MultiLawEvaluationError("M10D requires TOP_K >= 5 to measure Top-1/3/5")
    try:
        result = retrieve.retrieve(question.question, collection=collection, client=client, model=model, top_k=top_k)
    except retrieve.RetrievalError as exc:
        return QuestionResult(
            id=question.id, question=question.question, dataset=question.dataset,
            expected_sources=tuple(sorted(str(k) for k in expected)),
            expected_legislations=tuple(sorted(question.expected_legislations)),
            case_type=question.case_type, difficulty=question.difficulty, ranks=(),
            any_source_hit_at_1=False, any_source_hit_at_3=False, any_source_hit_at_5=False,
            all_sources_match_at_1=False, all_sources_match_at_3=False, all_sources_match_at_5=False,
            first_expected_source_rank=None,
            expected_legislation_hit_at_1=False, expected_legislation_hit_at_3=False, expected_legislation_hit_at_5=False,
            top1_legislation=None, non_expected_legislation_count_at_5=0, non_expected_legislation_share_at_5=None,
            embedding_tokens=None, retrieval_latency_ms=None,
            error_type=type(exc).__name__, safe_error="Retrieval failed for this question.",
        )

    ranks = _extract_rank_info(result.results)
    non_exp_count, non_exp_share = _non_expected_legislation_stats(question.expected_legislations, ranks, k=5)

    return QuestionResult(
        id=question.id, question=question.question, dataset=question.dataset,
        expected_sources=tuple(sorted(str(k) for k in expected)),
        expected_legislations=tuple(sorted(question.expected_legislations)),
        case_type=question.case_type, difficulty=question.difficulty, ranks=tuple(ranks),
        any_source_hit_at_1=_any_hit(expected, ranks, 1),
        any_source_hit_at_3=_any_hit(expected, ranks, 3),
        any_source_hit_at_5=_any_hit(expected, ranks, 5),
        all_sources_match_at_1=_all_match(expected, ranks, 1),
        all_sources_match_at_3=_all_match(expected, ranks, 3),
        all_sources_match_at_5=_all_match(expected, ranks, 5),
        first_expected_source_rank=_first_expected_source_rank(expected, ranks),
        expected_legislation_hit_at_1=_legislation_hit(question.expected_legislations, ranks, 1),
        expected_legislation_hit_at_3=_legislation_hit(question.expected_legislations, ranks, 3),
        expected_legislation_hit_at_5=_legislation_hit(question.expected_legislations, ranks, 5),
        top1_legislation=ranks[0].legislation_number if ranks else None,
        non_expected_legislation_count_at_5=non_exp_count,
        non_expected_legislation_share_at_5=non_exp_share,
        embedding_tokens=result.embedding_usage.total_tokens,
        retrieval_latency_ms=result.latency_ms,
        error_type=None, safe_error=None,
    )


def evaluate_all(
    questions: list[MultiLawQuestion], *, collection: Collection, client: Any = None,
    model: str = config.EMBEDDING_MODEL, top_k: int = EVAL_TOP_K,
) -> list[QuestionResult]:
    """Evaluate every question once, in order. A single question's
    retrieval error does not abort the batch (mirrors `evaluate_e2e`)."""
    return [evaluate_question(q, collection=collection, client=client, model=model, top_k=top_k) for q in questions]


# ============================================================================
# Aggregate summaries (§25-§27)
# ============================================================================


def _rate(results: list[QuestionResult], attr: str) -> float:
    if not results:
        raise MultiLawEvaluationError("Cannot compute a rate over zero results")
    return sum(1 for r in results if getattr(r, attr)) / len(results)


def summarize_group(results: list[QuestionResult]) -> dict[str, Any]:
    """Aggregate metrics for one group of QuestionResults (a law subset,
    the combined benchmark, a case_type, or a difficulty bucket)."""
    if not results:
        raise MultiLawEvaluationError("Cannot summarize zero results")
    shares = [r.non_expected_legislation_share_at_5 for r in results if r.non_expected_legislation_share_at_5 is not None]
    top1_unexpected = [
        r for r in results if r.top1_legislation is not None and r.top1_legislation not in r.expected_legislations
    ]
    top1_known = [r for r in results if r.top1_legislation is not None]
    return {
        "total_questions": len(results),
        "any_qualified_recall_at_1": _rate(results, "any_source_hit_at_1"),
        "any_qualified_recall_at_3": _rate(results, "any_source_hit_at_3"),
        "any_qualified_recall_at_5": _rate(results, "any_source_hit_at_5"),
        "all_qualified_match_at_1": _rate(results, "all_sources_match_at_1"),
        "all_qualified_match_at_3": _rate(results, "all_sources_match_at_3"),
        "all_qualified_match_at_5": _rate(results, "all_sources_match_at_5"),
        "legislation_hit_at_1": _rate(results, "expected_legislation_hit_at_1"),
        "legislation_hit_at_3": _rate(results, "expected_legislation_hit_at_3"),
        "legislation_hit_at_5": _rate(results, "expected_legislation_hit_at_5"),
        "top1_unexpected_legislation_count": len(top1_unexpected),
        "top1_unexpected_legislation_rate": (len(top1_unexpected) / len(top1_known)) if top1_known else None,
        "average_non_expected_legislation_share_at_5": (sum(shares) / len(shares)) if shares else None,
        "error_count": sum(1 for r in results if r.error_type is not None),
    }


def group_by(results: list[QuestionResult], attr: str) -> dict[str, list[QuestionResult]]:
    """Group results by a report dimension, omitting absent values."""
    grouped: dict[str, list[QuestionResult]] = {}
    for r in results:
        value = getattr(r, attr)
        if value is not None:
            grouped.setdefault(value, []).append(r)
    return grouped


def top1_legislation_confusion_matrix(results: list[QuestionResult]) -> dict[str, Any]:
    """§27: expected law (rows) vs retrieved Top-1 law (columns), restricted
    to single-expected-law questions (true for every M10D question - cross-
    law multi-source questions are out of scope, §12). Questions with no
    usable Top-1 legislation metadata or a retrieval error are counted
    separately, never silently folded into a cell.
    """
    laws = ("5326", "4458")
    matrix = {expected: {retrieved: 0 for retrieved in laws} for expected in laws}
    missing_top1 = 0
    errors = 0
    multi_law_expected = 0
    for r in results:
        if r.error_type is not None:
            errors += 1
            continue
        if len(r.expected_legislations) != 1:
            multi_law_expected += 1
            continue
        expected_law = r.expected_legislations[0]
        if r.top1_legislation not in laws:
            missing_top1 += 1
            continue
        matrix[expected_law][r.top1_legislation] += 1
    return {"matrix": matrix, "missing_top1_metadata": missing_top1, "retrieval_errors": errors, "multi_law_expected_excluded": multi_law_expected}


def failure_cases(results: list[QuestionResult]) -> list[dict[str, Any]]:
    """§28: questions needing human attention - safe diagnostic fields only."""
    cases = []
    for r in results:
        reasons = []
        if r.error_type is not None:
            reasons.append("retrieval_error")
        if not r.any_source_hit_at_5:
            reasons.append("expected_source_absent_from_top5")
        if not r.all_sources_match_at_5 and len(r.expected_sources) > 1:
            reasons.append("not_all_expected_sources_retrieved")
        if r.top1_legislation is not None and r.top1_legislation not in r.expected_legislations:
            reasons.append("top1_law_not_expected")
        if r.non_expected_legislation_share_at_5 is not None and r.non_expected_legislation_share_at_5 >= 0.6:
            reasons.append("high_non_expected_legislation_share")
        if reasons:
            cases.append({
                "id": r.id, "question": r.question, "expected_sources": list(r.expected_sources),
                "retrieved_top5_qualified_source_keys": [
                    str(rank.qualified_source_key) if rank.qualified_source_key else None for rank in r.ranks
                ],
                "first_expected_source_rank": r.first_expected_source_rank,
                "top1_legislation": r.top1_legislation, "diagnostic_reasons": reasons,
            })
    return cases


# ============================================================================
# Frozen 5326 historical PRE-expansion comparison (§23, §23B, §24)
# ============================================================================


def load_frozen_m9b_provisional(path: str | Path = M9B_PROVISIONAL_PATH) -> dict[str, Any]:
    """Read-only load of the frozen M9B artifact - never regenerated,
    never re-run against a recreated old collection (§23B)."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_5326_chunk_type_lookup(path: str | Path = CHUNKS_5326_PATH) -> dict[str, tuple[str, str, str]]:
    """chunk_id -> (legislation_number, article_type, article_no) from the
    real, unchanged 5326 Chunk records - a lookup against trusted persisted
    metadata, not string-parsing of `chunk_id` or inference from prose."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {c["chunk_id"]: (c["legislation_number"], c["article_type"], c["article_no"]) for c in data["chunks"]}


def historical_5326_question_outcomes(
    provisional: dict[str, Any] | None = None,
    chunk_lookup: dict[str, tuple[str, str, str]] | None = None,
) -> dict[str, dict[str, bool]]:
    """Deterministically derive PRE-4458-expansion Hit@K/ALL-match@K per
    question from the frozen `m9b-provisional.json` artifact (§23B).

    The artifact's `retrieved_articles` field stores only a raw article_no
    per rank, which is ambiguous for the 4 non-`normal` 5326 Chunks (1 `ek`
    + 3 `gecici`, each sharing a number with a `normal` Article). This
    function instead reconstructs each historical rank's true
    QualifiedSourceKey via `retrieved_chunk_ids` joined against
    `build_5326_chunk_type_lookup()` - never re-running retrieval.
    """
    if provisional is None:
        provisional = load_frozen_m9b_provisional()
    if chunk_lookup is None:
        chunk_lookup = build_5326_chunk_type_lookup()

    outcomes: dict[str, dict[str, bool]] = {}
    for r in provisional["results"]:
        expected = frozenset(QualifiedSourceKey.build("5326", "normal", a) for a in r["expected_articles"])
        keys_in_rank_order: list[QualifiedSourceKey | None] = []
        for chunk_id in r["retrieved_chunk_ids"]:
            resolved = chunk_lookup.get(chunk_id)
            if resolved is None:
                raise MultiLawEvaluationError("Historical chunk metadata is missing")
            keys_in_rank_order.append(QualifiedSourceKey.build(*resolved))

        def _any(k: int, keys: list[QualifiedSourceKey | None] = keys_in_rank_order) -> bool:
            return any(key in expected for key in keys[:k] if key is not None)

        def _all(k: int, keys: list[QualifiedSourceKey | None] = keys_in_rank_order) -> bool:
            got = {key for key in keys[:k] if key is not None}
            return expected.issubset(got)

        if r["id"] in outcomes:
            raise MultiLawEvaluationError("Duplicate historical question ID")
        outcomes[r["id"]] = {
            "any_hit_at_1": _any(1), "any_hit_at_3": _any(3), "any_hit_at_5": _any(5),
            "all_match_at_1": _all(1), "all_match_at_3": _all(3), "all_match_at_5": _all(5),
        }
    return outcomes


def compare_5326_regression(post_results: list[QuestionResult], historical: dict[str, dict[str, bool]]) -> dict[str, Any]:
    """§23: pre vs post rates + deltas + regression/improvement ID lists at
    K=1/3/5, for both ANY-hit and ALL-match. `post_results` must be exactly
    the 45 frozen-5326-subset QuestionResults from the current POST run."""
    by_id = {r.id: r for r in post_results}
    if len(by_id) != len(post_results) or set(by_id) != set(historical):
        raise MultiLawEvaluationError("Historical and post question IDs must match exactly")
    common_ids = sorted(set(historical) & set(by_id))
    if not common_ids:
        raise MultiLawEvaluationError("No overlapping question IDs between historical and post results")

    comparison: dict[str, Any] = {"question_count": len(common_ids)}
    for metric_name, post_attr in (("any_hit", "any_source_hit_at_"), ("all_match", "all_sources_match_at_")):
        metric_block: dict[str, Any] = {}
        for k in (1, 3, 5):
            hist_key = f"{metric_name}_at_{k}"
            pre_hits = {qid for qid in common_ids if historical[qid][hist_key]}
            post_hits = {qid for qid in common_ids if getattr(by_id[qid], f"{post_attr}{k}")}
            pre_rate = len(pre_hits) / len(common_ids)
            post_rate = len(post_hits) / len(common_ids)
            metric_block[f"k{k}"] = {
                "pre": pre_rate, "post": post_rate, "delta_pp": (post_rate - pre_rate) * 100,
                "pre_hit_post_miss_ids": sorted(pre_hits - post_hits),
                "pre_miss_post_hit_ids": sorted(post_hits - pre_hits),
            }
        comparison[metric_name] = metric_block
    return comparison


# ============================================================================
# Report writing (§29-§30)
# ============================================================================


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _question_result_to_dict(r: QuestionResult) -> dict[str, Any]:
    return {
        "id": r.id, "question": r.question, "dataset": r.dataset,
        "expected_sources": list(r.expected_sources), "expected_legislations": list(r.expected_legislations),
        "case_type": r.case_type, "difficulty": r.difficulty,
        "ranks": [
            {
                "rank": rank.rank, "chunk_id": rank.chunk_id, "legislation_number": rank.legislation_number,
                "article_type": rank.article_type, "article_no": rank.article_no,
                "qualified_source_key": str(rank.qualified_source_key) if rank.qualified_source_key else None,
                "distance": rank.distance,
            }
            for rank in r.ranks
        ],
        "any_source_hit_at_1": r.any_source_hit_at_1, "any_source_hit_at_3": r.any_source_hit_at_3, "any_source_hit_at_5": r.any_source_hit_at_5,
        "all_sources_match_at_1": r.all_sources_match_at_1, "all_sources_match_at_3": r.all_sources_match_at_3, "all_sources_match_at_5": r.all_sources_match_at_5,
        "first_expected_source_rank": r.first_expected_source_rank,
        "expected_legislation_hit_at_1": r.expected_legislation_hit_at_1, "expected_legislation_hit_at_3": r.expected_legislation_hit_at_3, "expected_legislation_hit_at_5": r.expected_legislation_hit_at_5,
        "top1_legislation": r.top1_legislation,
        "non_expected_legislation_count_at_5": r.non_expected_legislation_count_at_5,
        "non_expected_legislation_share_at_5": r.non_expected_legislation_share_at_5,
        "embedding_tokens": r.embedding_tokens, "retrieval_latency_ms": r.retrieval_latency_ms,
        "error_type": r.error_type, "safe_error": r.safe_error,
    }


def write_json_report(report: dict[str, Any], path: Path = JSON_REPORT_PATH) -> None:
    """Write the evaluation report to its designated JSON artifact."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv_report(results: list[QuestionResult], path: Path = CSV_REPORT_PATH) -> None:
    """Write per-question metrics to the designated CSV artifact."""
    fields = [
        "id", "dataset", "question", "expected_sources", "case_type", "difficulty",
        "top1_qualified_source_key", "top1_legislation", "first_expected_source_rank",
        "any_source_hit_at_1", "any_source_hit_at_3", "any_source_hit_at_5",
        "all_sources_match_at_1", "all_sources_match_at_3", "all_sources_match_at_5",
        "expected_legislation_hit_at_1", "expected_legislation_hit_at_3", "expected_legislation_hit_at_5",
        "non_expected_legislation_count_at_5", "non_expected_legislation_share_at_5",
        "top5_qualified_source_keys", "embedding_tokens", "retrieval_latency_ms", "error_type", "safe_error",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for r in results:
            top5_keys = [str(rank.qualified_source_key) if rank.qualified_source_key else "?" for rank in r.ranks]
            writer.writerow({
                "id": r.id, "dataset": r.dataset, "question": r.question,
                "expected_sources": " | ".join(r.expected_sources), "case_type": r.case_type, "difficulty": r.difficulty,
                "top1_qualified_source_key": top5_keys[0] if top5_keys else None, "top1_legislation": r.top1_legislation,
                "first_expected_source_rank": r.first_expected_source_rank,
                "any_source_hit_at_1": r.any_source_hit_at_1, "any_source_hit_at_3": r.any_source_hit_at_3, "any_source_hit_at_5": r.any_source_hit_at_5,
                "all_sources_match_at_1": r.all_sources_match_at_1, "all_sources_match_at_3": r.all_sources_match_at_3, "all_sources_match_at_5": r.all_sources_match_at_5,
                "expected_legislation_hit_at_1": r.expected_legislation_hit_at_1, "expected_legislation_hit_at_3": r.expected_legislation_hit_at_3, "expected_legislation_hit_at_5": r.expected_legislation_hit_at_5,
                "non_expected_legislation_count_at_5": r.non_expected_legislation_count_at_5,
                "non_expected_legislation_share_at_5": r.non_expected_legislation_share_at_5,
                "top5_qualified_source_keys": " | ".join(top5_keys), "embedding_tokens": r.embedding_tokens,
                "retrieval_latency_ms": r.retrieval_latency_ms, "error_type": r.error_type, "safe_error": r.safe_error,
            })


# ============================================================================
# CLI (manual/local validation only - see module docstring)
# ============================================================================


def _real_run_opt_in() -> bool:
    return bool(config.OPENAI_API_KEY) and os.getenv("RUN_OPENAI_INTEGRATION_TESTS") == "1"


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.1f}%"


def _collection_law_counts(collection: Collection) -> dict[str, int]:
    """Read per-law counts without filtering or changing collection records."""
    counts: dict[str, int] = {}
    for metadata in collection.get(include=["metadatas"])["metadatas"]:
        if not isinstance(metadata, dict):
            raise MultiLawEvaluationError("Collection source metadata is missing")
        key = QualifiedSourceKey.build(
            metadata.get("legislation_number"), metadata.get("article_type"), metadata.get("article_no")
        )
        counts[key.legislation_number] = counts.get(key.legislation_number, 0) + 1
    return counts


def main(argv: list[str] | None = None) -> None:
    """Manual/local real M10D benchmark run - NOT part of the automated test
    suite. Opens the EXISTING production collection, verifies its
    total/per-law counts before AND after (never mutates it - retrieval
    only), runs the combined 75-question benchmark exactly once per
    question, and writes the report artifacts. Only runs when explicit
    opt-in is enabled (see `_real_run_opt_in`)."""
    if not _real_run_opt_in():
        print(
            "Real M10D benchmark skipped: requires both OPENAI_API_KEY and "
            "RUN_OPENAI_INTEGRATION_TESTS=1 (explicit opt-in not enabled or "
            "credentials unavailable)."
        )
        return

    from src import index

    if EVAL_TOP_K < 5:
        raise MultiLawEvaluationError("M10D requires TOP_K >= 5 to measure Top-1/3/5")
    questions = load_combined_benchmark()
    validate_4458_sources_against_corpus([q for q in questions if q.dataset == "4458"])
    historical = historical_5326_question_outcomes()
    client = index.get_client()
    collection = client.get_collection(name=config.COLLECTION_NAME, embedding_function=None)
    count_before = collection.count()
    if count_before != 329:
        print(f"Real M10D benchmark aborted: collection count is {count_before}, expected 329.", file=sys.stderr)
        return

    law_counts_before = _collection_law_counts(collection)
    if law_counts_before != {"5326": 53, "4458": 276}:
        raise MultiLawEvaluationError("Production per-law collection counts do not match M10C")

    results = evaluate_all(questions, collection=collection)
    count_after = collection.count()
    law_counts_after = _collection_law_counts(collection)
    if count_after != count_before or law_counts_after != law_counts_before:
        raise MultiLawEvaluationError("Collection counts changed during evaluation")

    results_5326 = [r for r in results if r.dataset == "5326"]
    results_4458 = [r for r in results if r.dataset == "4458"]

    regression = compare_5326_regression(results_5326, historical)

    summary_5326 = summarize_group(results_5326)
    summary_4458 = summarize_group(results_4458)
    summary_combined = summarize_group(results)

    case_type_breakdown = {name: summarize_group(group) for name, group in sorted(group_by(results_4458, "case_type").items())}
    difficulty_breakdown = {name: summarize_group(group) for name, group in sorted(group_by(results_4458, "difficulty").items())}
    confusion = top1_legislation_confusion_matrix(results)
    failures = failure_cases(results)

    total_embedding_tokens = sum(r.embedding_tokens for r in results if r.embedding_tokens is not None)

    report = {
        "metadata": {
            "run_timestamp": datetime.now(timezone.utc).isoformat(),
            "collection_name": config.COLLECTION_NAME,
            "collection_count_before": count_before,
            "collection_count_after": count_after,
            "collection_law_counts_before": law_counts_before,
            "collection_law_counts_after": law_counts_after,
            "embedding_model": config.EMBEDDING_MODEL,
            "top_k": EVAL_TOP_K,
            "distance_metric": retrieve.distance_metric(collection),
            "dataset_paths": {
                "seed_5326": str(SEED_5326_PATH.relative_to(PROJECT_ROOT)),
                "extension_5326": str(EXTENSION_5326_PATH.relative_to(PROJECT_ROOT)),
                "frozen_4458": str(QUESTIONS_4458_PATH.relative_to(PROJECT_ROOT)),
            },
            "dataset_sha256": {
                "seed_5326": _sha256(SEED_5326_PATH), "extension_5326": _sha256(EXTENSION_5326_PATH),
                "m9b_provisional": _sha256(M9B_PROVISIONAL_PATH), "frozen_4458": _sha256(QUESTIONS_4458_PATH),
            },
            "generation_calls": 0, "generation_tokens": 0, "total_query_embedding_tokens": total_embedding_tokens,
        },
        "frozen_5326_regression_comparison": regression,
        "summary_5326": summary_5326, "summary_4458": summary_4458, "summary_combined": summary_combined,
        "case_type_breakdown_4458": case_type_breakdown, "difficulty_breakdown_4458": difficulty_breakdown,
        "top1_legislation_confusion_matrix": confusion, "failure_cases": failures,
        "results": [_question_result_to_dict(r) for r in results],
    }
    write_json_report(report)
    write_csv_report(results)

    print(f"Collection count before/after: {count_before}/{count_after}")
    print(f"5326  ANY@1/3/5:  {_pct(summary_5326['any_qualified_recall_at_1'])} / {_pct(summary_5326['any_qualified_recall_at_3'])} / {_pct(summary_5326['any_qualified_recall_at_5'])}")
    print(f"4458  ANY@1/3/5:  {_pct(summary_4458['any_qualified_recall_at_1'])} / {_pct(summary_4458['any_qualified_recall_at_3'])} / {_pct(summary_4458['any_qualified_recall_at_5'])}")
    print(f"COMBINED ANY@1/3/5: {_pct(summary_combined['any_qualified_recall_at_1'])} / {_pct(summary_combined['any_qualified_recall_at_3'])} / {_pct(summary_combined['any_qualified_recall_at_5'])}")
    print(f"Reports: {JSON_REPORT_PATH} | {CSV_REPORT_PATH}")
    if count_before != 329 or count_after != 329:
        print("WARNING: collection count invariant (329) failed.", file=sys.stderr)


if __name__ == "__main__":
    main()
