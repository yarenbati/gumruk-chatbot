"""
Offline retrieval-quality evaluation (Milestone M5B): `tests/questions.json`
-> `retrieve.retrieve()` -> Recall@K / Hit@K metrics.

Scope: measure the HONEST M5A retrieval baseline against the seed evaluation
set. This module does NOT implement an LLM call, does NOT generate an
answer, does NOT tune retrieval (see module docstring notes below and the
M5B task scope), and does NOT modify `tests/questions.json` - that file is
read-only here.

Module boundary: evaluation logic lives ENTIRELY in this module, separate
from production retrieval (`src/retrieve.py`). `src/retrieve.py` is never
modified to accommodate metrics, and `src/generate.py` (future LLM answer
generation) is untouched and unreferenced.

Metric terminology (IMPORTANT - read before interpreting any number this
module prints):

The project reports "Recall@K" for consistency with `docs/evaluation.md`,
but the metric actually computed is QUESTION-LEVEL ANY-MATCH RECALL@K, not
classical set-level recall for multi-label retrieval:

    E   = normalize(question.expected_articles)          (a set)
    R_k = normalize(article_no of the first K retrieved chunks)  (a set)

    ANY-match hit at K  <=>  E ∩ R_k != ∅   (question-level Hit@K / Success@K)
    ALL-match hit at K  <=>  E ⊆ R_k        (every expected article present)

For the current 15 seed questions every `expected_articles` has exactly one
element, so ANY-match and ALL-match necessarily coincide; both are still
computed correctly and independently so a future multi-article question
is handled correctly without further changes.

Article-number matching (see `normalize_article_no`) is done via a single,
explicit normalization function applied identically to both `expected_articles`
and every retrieved `article_no` - chunk_id is never used as the ground-truth
matcher, since chunk_id is an indexing-internal identifier, not the domain
concept (`article_no`) the evaluation set is written against.

Retrieval cost control (docs §5): `retrieve(question, top_k=5)` is called
EXACTLY ONCE per question. Top-1/Top-3/Top-5 are all derived by slicing the
same ranked Top-5 result - never three separate retrievals per question.

No tuning: this module NEVER changes `EMBEDDING_MODEL`, `MAX_CHUNK_CHARS`,
the Chroma distance metric, `TOP_K`, indexed embeddings, `Chunk.text`, query
wording, or `tests/questions.json` in response to a measured score. A low
Recall is a project finding to report, not a defect to hide or work around
here (reranking/hybrid-search/BM25/query-expansion/thresholds are explicitly
out of scope for this module).

Security: the OpenAI API key is read only from `src.config.OPENAI_API_KEY`;
this module never prints the key, full embedding vectors, or full legal
document text.

CLI usage (manual/local validation only - not part of the automated test
suite; requires BOTH `OPENAI_API_KEY` and `RUN_OPENAI_INTEGRATION_TESTS=1` to
run real retrieval, mirroring src/retrieve.py's/src/embed.py's/src/index.py's
gate - the reusable metric functions below carry NO such gate):
    RUN_OPENAI_INTEGRATION_TESTS=1 python -m src.evaluate tests/questions.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from chromadb.api.models.Collection import Collection

from src import config, retrieve

if __name__ == "__main__":  # pragma: no cover - exercised via CLI, not tests
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_QUESTIONS_PATH = PROJECT_ROOT / "tests" / "questions.json"

# Fixed evaluation depth (docs §5/§10): retrieve() is called with top_k=5
# exactly once per question; Top-1/Top-3/Top-5 are all sliced from that one
# ranked result. Changing this is a tuning decision and is out of scope here.
EVAL_TOP_K = 5


class EvaluationError(RuntimeError):
    """Raised for malformed evaluation input (a question missing/blank
    id/question/expected_articles, a non-list/empty expected_articles, a
    malformed question-set file) or when metrics are requested over zero
    questions. Never silently evaluates malformed ground truth and never
    divides by zero.
    """


# ============================================================================
# Article number normalization
# ============================================================================


def normalize_article_no(article_no: str) -> str:
    """Canonicalize one article number for ground-truth matching.

    Rule, applied in this exact order:
      1. must be a `str` (raises `EvaluationError` otherwise)
      2. strip leading/trailing whitespace
      3. lowercase
      4. convert "-" and "_" separator characters to "/"
      5. collapse any whitespace immediately around a "/" separator
         (so "42 / A", "42/ A", "42 /A" all normalize the same as "42/A")
      6. strip again (defensive, in case step 5 left edge whitespace)

    Examples: "42/A" -> "42/a", "42-a" -> "42/a", "42_A" -> "42/a",
    "  42 / A  " -> "42/a". Unrelated article numbers are never merged:
    only the separator/case is normalized - digits and letters themselves
    are never reordered, truncated, or substituted, so "42" and "43" (or
    "42/a" and "42/b") remain distinct after normalization.
    """
    if not isinstance(article_no, str):
        raise EvaluationError(f"article number must be a str, got {type(article_no).__name__}")
    normalized = article_no.strip().lower()
    normalized = re.sub(r"[-_]", "/", normalized)
    normalized = re.sub(r"\s*/\s*", "/", normalized)
    return normalized.strip()


# ============================================================================
# Question set loading/validation (tests/questions.json is READ-ONLY)
# ============================================================================


@dataclass(frozen=True)
class EvaluationQuestion:
    """One validated evaluation question (read-only view of one
    tests/questions.json entry) - never written back to disk."""

    id: str
    question: str
    expected_articles: tuple[str, ...]
    normalized_expected_articles: frozenset[str]


def _validate_and_build_question(raw: Any, *, index: int) -> EvaluationQuestion:
    if not isinstance(raw, dict):
        raise EvaluationError(f"Question at index {index} must be a JSON object, got {type(raw).__name__}")

    qid = raw.get("id")
    if not isinstance(qid, str) or not qid.strip():
        raise EvaluationError(f"Question at index {index} has a missing/empty 'id'")

    question_text = raw.get("question")
    if not isinstance(question_text, str) or not question_text.strip():
        raise EvaluationError(f"Question {qid!r} has a missing/empty 'question'")

    expected = raw.get("expected_articles")
    if not isinstance(expected, list) or len(expected) == 0:
        raise EvaluationError(f"Question {qid!r} has a missing/empty 'expected_articles'")
    if not all(isinstance(a, str) and a.strip() for a in expected):
        raise EvaluationError(f"Question {qid!r} has a non-string or empty entry in 'expected_articles'")

    # Duplicate normalized expected articles may be deduplicated for metric
    # calculation (docs §7) - a plain set is enough, order is irrelevant for
    # ANY/ALL-match set membership.
    normalized = frozenset(normalize_article_no(a) for a in expected)

    return EvaluationQuestion(
        id=qid,
        question=question_text,
        expected_articles=tuple(expected),
        normalized_expected_articles=normalized,
    )


def load_questions(path: str | Path = DEFAULT_QUESTIONS_PATH) -> list[EvaluationQuestion]:
    """Load and validate an evaluation question set (default:
    `tests/questions.json`) WITHOUT ever modifying the source file - this
    function only reads `path`; `expert_validated=false` entries are loaded
    as-is and are never rewritten to `true`.

    Every question must have a non-empty string `id`, a non-empty string
    `question`, and a non-empty list of non-empty string `expected_articles`
    - malformed ground truth raises `EvaluationError` rather than being
    silently evaluated. An empty question set also raises `EvaluationError`
    (there is nothing to divide by when computing a rate over zero
    questions).
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise EvaluationError(f"Expected a JSON list of questions in {path}, got {type(data).__name__}")
    if not data:
        raise EvaluationError(f"Question set {path} is empty - cannot evaluate zero questions")

    return [_validate_and_build_question(raw, index=i) for i, raw in enumerate(data)]


# ============================================================================
# Per-question metric computation (pure - no Chroma/OpenAI dependency)
# ============================================================================


@dataclass(frozen=True)
class QuestionEvaluation:
    """One question's evaluation outcome against its Top-5 ranked
    retrieval. `retrieved_*` fields are in rank order (index 0 = rank 1) and
    are diagnostics only - `first_expected_rank`/hit flags are the metric
    fields actually aggregated by `summarize`.
    """

    question_id: str
    question: str
    expected_articles: tuple[str, ...]
    normalized_expected_articles: frozenset[str]
    retrieved_chunk_ids: tuple[str, ...]
    retrieved_article_nos: tuple[str | None, ...]
    retrieved_distances: tuple[float, ...]
    first_expected_rank: int | None
    any_hit_at_1: bool
    any_hit_at_3: bool
    any_hit_at_5: bool
    all_hit_at_1: bool
    all_hit_at_3: bool
    all_hit_at_5: bool


def evaluate_question(
    question: EvaluationQuestion,
    *,
    retrieved_article_nos: list[str | None],
    retrieved_chunk_ids: list[str] | None = None,
    retrieved_distances: list[float] | None = None,
) -> QuestionEvaluation:
    """Compute ANY-match/ALL-match hit flags and the first expected-article
    rank for one question, given its Top-5 ranked retrieval output - pure
    metric math, no retrieval call happens here.

    `retrieved_article_nos` must be in rank order (index 0 = rank 1) and
    holds the RAW (un-normalized) `article_no` metadata value per retrieved
    chunk; normalization (`normalize_article_no`) is applied internally,
    once, identically to both sides. A `None` entry (a result missing
    `article_no` metadata) never matches any expected article.

    Recall matching is article-level and set-based for ANY/ALL-match (docs
    §12): multiple retrieved chunks from the same article never inflate a
    match. `first_expected_rank`, however, is always computed from the FULL
    ranked list before any such de-duplication - it is the true first rank
    at which an expected article appears, never collapsed.
    """
    if retrieved_chunk_ids is None:
        retrieved_chunk_ids = ["" for _ in retrieved_article_nos]
    if retrieved_distances is None:
        retrieved_distances = []

    normalized_expected = question.normalized_expected_articles

    first_rank: int | None = None
    for rank, raw_article in enumerate(retrieved_article_nos, start=1):
        if raw_article is None:
            continue
        if normalize_article_no(raw_article) in normalized_expected:
            first_rank = rank
            break

    def _any_hit(k: int) -> bool:
        return first_rank is not None and first_rank <= k

    def _all_hit(k: int) -> bool:
        top_k_normalized = {normalize_article_no(a) for a in retrieved_article_nos[:k] if a is not None}
        return normalized_expected.issubset(top_k_normalized)

    return QuestionEvaluation(
        question_id=question.id,
        question=question.question,
        expected_articles=question.expected_articles,
        normalized_expected_articles=normalized_expected,
        retrieved_chunk_ids=tuple(retrieved_chunk_ids),
        retrieved_article_nos=tuple(retrieved_article_nos),
        retrieved_distances=tuple(retrieved_distances),
        first_expected_rank=first_rank,
        any_hit_at_1=_any_hit(1),
        any_hit_at_3=_any_hit(3),
        any_hit_at_5=_any_hit(5),
        all_hit_at_1=_all_hit(1),
        all_hit_at_3=_all_hit(3),
        all_hit_at_5=_all_hit(5),
    )


# ============================================================================
# Aggregate summary
# ============================================================================


@dataclass(frozen=True)
class EvaluationSummary:
    """Aggregate metrics across all evaluated questions.

    `any_recall_at_*`/`all_match_at_*` are exact fractions (`count / total`,
    computed once with no intermediate rounding) - format to a percentage
    only at print time. The four `rank_*_count` fields are an EXCLUSIVE,
    non-overlapping partition of `total_questions` (docs §11): every
    question falls into exactly one of them, so they always sum to
    `total_questions` regardless of how `first_expected_rank` is
    distributed.
    """

    total_questions: int
    any_hit_count_at_1: int
    any_hit_count_at_3: int
    any_hit_count_at_5: int
    all_hit_count_at_1: int
    all_hit_count_at_3: int
    all_hit_count_at_5: int
    any_recall_at_1: float
    any_recall_at_3: float
    any_recall_at_5: float
    all_match_at_1: float
    all_match_at_3: float
    all_match_at_5: float
    rank_1_count: int
    rank_2_3_count: int
    rank_4_5_count: int
    not_in_top5_count: int
    question_results: tuple[QuestionEvaluation, ...]


def summarize(question_evaluations: list[QuestionEvaluation]) -> EvaluationSummary:
    """Aggregate a list of per-question evaluations into `EvaluationSummary`.

    Raises `EvaluationError` for an empty list rather than dividing by zero.

    The exclusive rank-distribution bins are derived from the `any_hit_at_*`
    flags rather than raw equality on `first_expected_rank` against 1/3/5,
    so the four bins (`rank_1`, `rank_2_3`, `rank_4_5`, `not_in_top5`)
    always sum to `total_questions` even if a caller supplied a ranked list
    shorter or longer than the standard Top-5 window.
    """
    total = len(question_evaluations)
    if total == 0:
        raise EvaluationError("Cannot summarize zero question evaluations")

    def _count(predicate: Any) -> int:
        return sum(1 for qe in question_evaluations if predicate(qe))

    any1 = _count(lambda qe: qe.any_hit_at_1)
    any3 = _count(lambda qe: qe.any_hit_at_3)
    any5 = _count(lambda qe: qe.any_hit_at_5)
    all1 = _count(lambda qe: qe.all_hit_at_1)
    all3 = _count(lambda qe: qe.all_hit_at_3)
    all5 = _count(lambda qe: qe.all_hit_at_5)

    rank_1 = _count(lambda qe: qe.any_hit_at_1)
    rank_2_3 = _count(lambda qe: qe.any_hit_at_3 and not qe.any_hit_at_1)
    rank_4_5 = _count(lambda qe: qe.any_hit_at_5 and not qe.any_hit_at_3)
    not_in_top5 = _count(lambda qe: not qe.any_hit_at_5)

    return EvaluationSummary(
        total_questions=total,
        any_hit_count_at_1=any1,
        any_hit_count_at_3=any3,
        any_hit_count_at_5=any5,
        all_hit_count_at_1=all1,
        all_hit_count_at_3=all3,
        all_hit_count_at_5=all5,
        any_recall_at_1=any1 / total,
        any_recall_at_3=any3 / total,
        any_recall_at_5=any5 / total,
        all_match_at_1=all1 / total,
        all_match_at_3=all3 / total,
        all_match_at_5=all5 / total,
        rank_1_count=rank_1,
        rank_2_3_count=rank_2_3,
        rank_4_5_count=rank_4_5,
        not_in_top5_count=not_in_top5,
        question_results=tuple(question_evaluations),
    )


def human_review_flags(summary: EvaluationSummary) -> list[QuestionEvaluation]:
    """Questions whose expected article did not appear anywhere in Top-5 -
    flagged for HUMAN REVIEW only (docs §13). This never edits
    `expected_articles`, the question text, or `expert_validated`, and never
    auto-classifies the ground truth as wrong - it only surfaces the
    question so a human can judge retrieval-weakness vs. a possible
    ground-truth issue.
    """
    return [qe for qe in summary.question_results if not qe.any_hit_at_5]


# ============================================================================
# Orchestration (retrieve() is called exactly once per question)
# ============================================================================


def evaluate_all(
    questions: list[EvaluationQuestion],
    *,
    collection: Collection,
    client: Any = None,
    model: str = config.EMBEDDING_MODEL,
    top_k: int = EVAL_TOP_K,
) -> EvaluationSummary:
    """Run `retrieve.retrieve(question.question, top_k=top_k)` exactly ONCE
    per question (docs §5) and derive all K-cutoffs from that single ranked
    result - never three separate retrievals per question. Each question is
    embedded exactly once during one evaluation run.
    """
    question_evaluations: list[QuestionEvaluation] = []
    for question in questions:
        result = retrieve.retrieve(question.question, collection=collection, client=client, model=model, top_k=top_k)
        article_nos = [chunk.metadata.get("article_no") for chunk in result.results]
        chunk_ids = [chunk.chunk_id for chunk in result.results]
        distances = [chunk.distance for chunk in result.results]
        question_evaluations.append(
            evaluate_question(
                question,
                retrieved_article_nos=article_nos,
                retrieved_chunk_ids=chunk_ids,
                retrieved_distances=distances,
            )
        )
    return summarize(question_evaluations)


# ============================================================================
# CLI (manual/local validation only - see module docstring)
# ============================================================================


def _real_evaluation_opt_in() -> bool:
    """Explicit opt-in gate for the MANUAL CLI only - a real evaluation run
    (which embeds every question) is only ever made when BOTH
    `config.OPENAI_API_KEY` is available AND `RUN_OPENAI_INTEGRATION_TESTS=1`
    is set. This mirrors src/retrieve.py's/src/embed.py's/src/index.py's
    real-API gates. The reusable metric functions above carry no such gate.
    """
    return bool(config.OPENAI_API_KEY) and os.getenv("RUN_OPENAI_INTEGRATION_TESTS") == "1"


def _pct(fraction: float) -> str:
    return f"{fraction * 100:.1f}%"


def _format_top5(article_nos: tuple[str | None, ...]) -> str:
    return ", ".join(a if a is not None else "?" for a in article_nos)


def main(argv: list[str] | None = None) -> None:
    """Manual/local evaluation CLI - NOT part of the automated test suite.
    Loads a question set, opens the EXISTING real Chroma collection
    (read-only - never indexes, never alters the collection), runs
    `retrieve()` once per question, and prints compact metrics. Real
    retrieval only happens when explicit opt-in is enabled (see
    `_real_evaluation_opt_in`); otherwise exits cleanly before embedding.
    """
    from src import index  # local import: keeps `src.index`/chromadb client setup CLI-only here

    parser = argparse.ArgumentParser(description="Evaluate retrieval quality (Recall@K) against a question set.")
    parser.add_argument(
        "questions_json",
        nargs="?",
        type=Path,
        default=DEFAULT_QUESTIONS_PATH,
        help=f"Path to an evaluation questions JSON file (default: {DEFAULT_QUESTIONS_PATH})",
    )
    args = parser.parse_args(argv)

    if not _real_evaluation_opt_in():
        print(
            "Real evaluation skipped: requires both OPENAI_API_KEY and "
            "RUN_OPENAI_INTEGRATION_TESTS=1 (explicit opt-in not enabled or "
            "credentials unavailable)."
        )
        return

    questions = load_questions(args.questions_json)

    client = index.get_client()
    collection = index.get_collection(client)
    count = collection.count()
    if count == 0:
        print(f"Collection '{collection.name}' is empty - nothing to evaluate.")
        return

    print(f"Collection: {collection.name}")
    print(f"Collection count: {count}")
    print(f"Distance metric: {retrieve.distance_metric(collection)}")
    print(f"Embedding model: {config.EMBEDDING_MODEL}")
    print(f"Evaluation top_k: {EVAL_TOP_K}")
    print(f"Questions: {len(questions)}")
    print()

    summary = evaluate_all(questions, collection=collection, top_k=EVAL_TOP_K)

    print("ID   | Expected | First expected rank | Top-5 articles")
    for qe in summary.question_results:
        expected_str = ", ".join(qe.expected_articles)
        rank_str = str(qe.first_expected_rank) if qe.first_expected_rank is not None else "not in Top-5"
        print(f"{qe.question_id} | {expected_str} | {rank_str} | {_format_top5(qe.retrieved_article_nos)}")

    print()
    print(f"ANY-match Recall@1: {summary.any_hit_count_at_1}/{summary.total_questions} = {_pct(summary.any_recall_at_1)}")
    print(f"ANY-match Recall@3: {summary.any_hit_count_at_3}/{summary.total_questions} = {_pct(summary.any_recall_at_3)}")
    print(f"ANY-match Recall@5: {summary.any_hit_count_at_5}/{summary.total_questions} = {_pct(summary.any_recall_at_5)}")
    print(f"ALL-match@1: {summary.all_hit_count_at_1}/{summary.total_questions} = {_pct(summary.all_match_at_1)}")
    print(f"ALL-match@3: {summary.all_hit_count_at_3}/{summary.total_questions} = {_pct(summary.all_match_at_3)}")
    print(f"ALL-match@5: {summary.all_hit_count_at_5}/{summary.total_questions} = {_pct(summary.all_match_at_5)}")

    print()
    print("Cumulative:")
    print(f"  expected in Top-1: {summary.any_hit_count_at_1}")
    print(f"  expected in Top-3: {summary.any_hit_count_at_3}")
    print(f"  expected in Top-5: {summary.any_hit_count_at_5}")
    print(f"  not in Top-5: {summary.not_in_top5_count}")

    print()
    print("Exclusive first-hit distribution:")
    print(f"  rank 1: {summary.rank_1_count}")
    print(f"  rank 2-3: {summary.rank_2_3_count}")
    print(f"  rank 4-5: {summary.rank_4_5_count}")
    print(f"  not in Top-5: {summary.not_in_top5_count}")

    reviews = human_review_flags(summary)
    print()
    if not reviews:
        print("HUMAN REVIEW REQUIRED: none")
    else:
        print(f"HUMAN REVIEW REQUIRED ({len(reviews)}):")
        for qe in reviews:
            print(f"- {qe.question_id}: {qe.question}")
            print(f"  expected_articles: {list(qe.expected_articles)}")
            print(f"  Top-5 articles: {_format_top5(qe.retrieved_article_nos)}")
            print(f"  Top-5 chunk_ids: {', '.join(qe.retrieved_chunk_ids)}")
            if qe.retrieved_distances:
                print(f"  Top-5 distances: {', '.join(f'{d:.4f}' for d in qe.retrieved_distances)}")


if __name__ == "__main__":
    main()
