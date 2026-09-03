"""Deterministic end-to-end structural evaluation for the production RAG pipeline.

This module calls ``rag.run_rag`` exactly once per question. It does not judge
legal correctness, tune the pipeline, parse citations from answer prose, or use
an LLM as a judge. Human-review fields remain empty until a person fills them.
"""

from __future__ import annotations

import csv
import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Literal

from src import config, evaluate, generate, rag, retrieve

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_QUESTIONS_PATH = evaluate.DEFAULT_QUESTIONS_PATH
DEFAULT_JSON_REPORT = PROJECT_ROOT / "reports" / "evaluation" / "e2e-baseline.json"
DEFAULT_CSV_REPORT = PROJECT_ROOT / "reports" / "evaluation" / "e2e-baseline.csv"
M9B_JSON_REPORT = PROJECT_ROOT / "reports" / "evaluation" / "m9b-provisional.json"
M9B_CSV_REPORT = PROJECT_ROOT / "reports" / "evaluation" / "m9b-provisional.csv"
M9B_ANSWER_REVIEW = PROJECT_ROOT / "reports" / "evaluation" / "m9b-answer-review.csv"
M9B_QUESTION_REVIEW = PROJECT_ROOT / "reports" / "evaluation" / "m9b-question-review.csv"
FROZEN_RECALL = {1: 12 / 15, 3: 13 / 15, 5: 14 / 15}

RAGRunner = Callable[[str], rag.RAGResult]


@dataclass(frozen=True)
class HumanReview:
    """Blank human/expert grading fields; the evaluator never fills these."""

    legal_correctness: int | None = None
    completeness: int | None = None
    groundedness: int | None = None
    citation_relevance: int | None = None
    sufficiency_decision: str | None = None
    unsafe_overclaim: bool | None = None
    reviewer_notes: str | None = None

    @property
    def is_complete(self) -> bool:
        """Return whether every rubric field has actually been populated."""
        return all(
            value is not None
            for value in (
                self.legal_correctness,
                self.completeness,
                self.groundedness,
                self.citation_relevance,
                self.sufficiency_decision,
                self.unsafe_overclaim,
                self.reviewer_notes,
            )
        )


@dataclass(frozen=True)
class E2EQuestionResult:
    """Immutable structural evidence collected from one ``RAGResult``."""

    id: str
    question: str
    expected_articles: tuple[str, ...]
    expert_validated: bool
    retrieved_articles: tuple[str | None, ...]
    retrieved_chunk_ids: tuple[str, ...]
    expected_article_present: bool
    first_expected_rank: int | None
    all_expected_articles_retrieved: bool
    status: Literal["YETERLI", "YETERSIZ"] | None
    insufficient_context: bool | None
    answer: str | None
    cited_articles: tuple[str | None, ...]
    citation_count: int
    citation_labels_structurally_valid: bool | None
    expected_article_cited: bool
    all_expected_articles_cited: bool
    embedding_tokens: int | None
    generation_input_tokens: int | None
    generation_output_tokens: int | None
    generation_total_tokens: int | None
    retrieval_latency_ms: float | None
    generation_latency_ms: float | None
    pipeline_latency_ms: float | None
    error_type: str | None
    error_message_safe: str | None
    requires_priority_review: bool
    human_review: HumanReview = HumanReview()


@dataclass(frozen=True)
class E2ESummary:
    """Typed aggregate of descriptive structural, performance, and usage metrics."""

    total_questions: int
    completed_questions: int
    error_count: int
    expected_article_present_count: int
    expected_article_present_rate: float
    recall_at_1: float
    recall_at_3: float
    recall_at_5: float
    all_match_at_1: float
    all_match_at_3: float
    all_match_at_5: float
    all_expected_articles_retrieved_count: int
    all_expected_articles_retrieved_rate: float
    yeterli_count: int
    yetersiz_count: int
    answers_with_citations: int
    expected_article_cited_count: int
    expected_article_cited_rate: float
    all_expected_articles_cited_count: int
    all_expected_articles_cited_rate: float
    requires_priority_review_count: int
    requires_priority_review_rate: float
    human_review_completed_count: int
    human_review_pending_count: int
    average_retrieval_latency_ms: float | None
    average_generation_latency_ms: float | None
    average_pipeline_latency_ms: float | None
    total_embedding_tokens: int | None
    total_generation_input_tokens: int | None
    total_generation_output_tokens: int | None
    total_generation_tokens: int | None


@dataclass(frozen=True)
class RunMetadata:
    """Safe reproducibility metadata for a real baseline batch."""

    run_timestamp: str
    evaluation_question_count: int
    collection_name: str
    collection_count_before: int
    collection_count_after: int
    embedding_model: str
    llm_model: str
    top_k: int
    distance_metric: str | None
    dataset_path: str
    dataset_sha256: str


@dataclass(frozen=True)
class E2EBatchReport:
    """Machine-readable E2E batch report."""

    metadata: RunMetadata
    summary: E2ESummary
    results: tuple[E2EQuestionResult, ...]


@dataclass(frozen=True)
class FailureCase:
    """Safe compact structural failure/priority-review diagnostic."""

    id: str
    question: str
    expected_articles: tuple[str, ...]
    retrieved_articles: tuple[str | None, ...]
    status: str | None
    cited_articles: tuple[str | None, ...]


@dataclass(frozen=True)
class M9BProvisionalReport:
    """Typed M9B report with extension breakdowns and frozen-subset checks."""

    metadata: RunMetadata
    summary: E2ESummary
    m9a_subset_summary: E2ESummary
    case_type_breakdown: dict[str, E2ESummary]
    difficulty_breakdown: dict[str, E2ESummary]
    failure_cases: tuple[FailureCase, ...]
    results: tuple[E2EQuestionResult, ...]


def _article_values(values: list[object]) -> tuple[str | None, ...]:
    return tuple(value if isinstance(value, str) and value.strip() else None for value in values)


def _normalized(values: tuple[str | None, ...]) -> set[str]:
    return {evaluate.normalize_article_no(value) for value in values if value is not None}


def _failed_result(question: evaluate.EvaluationQuestion, exc: Exception) -> E2EQuestionResult:
    return E2EQuestionResult(
        id=question.id, question=question.question, expected_articles=question.expected_articles,
        expert_validated=question.expert_validated, retrieved_articles=(), retrieved_chunk_ids=(),
        expected_article_present=False, first_expected_rank=None, all_expected_articles_retrieved=False,
        status=None, insufficient_context=None, answer=None, cited_articles=(), citation_count=0,
        citation_labels_structurally_valid=None, expected_article_cited=False,
        all_expected_articles_cited=False, embedding_tokens=None, generation_input_tokens=None,
        generation_output_tokens=None, generation_total_tokens=None, retrieval_latency_ms=None,
        generation_latency_ms=None, pipeline_latency_ms=None, error_type=type(exc).__name__,
        error_message_safe="Pipeline failed during end-to-end evaluation.", requires_priority_review=True,
    )


def evaluate_question(
    question: evaluate.EvaluationQuestion,
    *,
    rag_runner: RAGRunner = rag.run_rag,
) -> E2EQuestionResult:
    """Run the production composition once and collect deterministic evidence."""
    try:
        result = rag_runner(question.question)
    except (retrieve.RetrievalError, generate.GenerationError, rag.RAGPipelineError) as exc:
        return _failed_result(question, exc)

    retrieved_articles = _article_values([chunk.metadata.get("article_no") for chunk in result.retrieval.results])
    expected = question.normalized_expected_articles
    retrieved_normalized = _normalized(retrieved_articles)
    first_rank = next(
        (rank for rank, article in enumerate(retrieved_articles, 1)
         if article is not None and evaluate.normalize_article_no(article) in expected),
        None,
    )
    cited_articles = _article_values([citation.article_no for citation in result.citations])
    cited_normalized = _normalized(cited_articles)
    expected_present = bool(expected & retrieved_normalized)
    expected_cited = bool(expected & cited_normalized)
    all_retrieved = expected.issubset(retrieved_normalized)
    all_cited = expected.issubset(cited_normalized)
    status: Literal["YETERLI", "YETERSIZ"] = "YETERSIZ" if result.insufficient_context else "YETERLI"
    requires_review = (
        not expected_present
        or status == "YETERSIZ"
        or (expected_present and not expected_cited)
        or (len(expected) > 1 and (not all_retrieved or not all_cited))
    )
    usage = result.generation.usage
    return E2EQuestionResult(
        id=question.id, question=question.question, expected_articles=question.expected_articles,
        expert_validated=question.expert_validated, retrieved_articles=retrieved_articles,
        retrieved_chunk_ids=tuple(chunk.chunk_id for chunk in result.retrieval.results),
        expected_article_present=expected_present, first_expected_rank=first_rank,
        all_expected_articles_retrieved=all_retrieved, status=status,
        insufficient_context=result.insufficient_context, answer=result.generation.answer,
        cited_articles=cited_articles, citation_count=len(result.citations),
        citation_labels_structurally_valid=True, expected_article_cited=expected_cited,
        all_expected_articles_cited=all_cited,
        embedding_tokens=result.retrieval.embedding_usage.total_tokens,
        generation_input_tokens=usage.input_tokens, generation_output_tokens=usage.output_tokens,
        generation_total_tokens=usage.total_tokens, retrieval_latency_ms=result.retrieval.latency_ms,
        generation_latency_ms=result.generation.latency_ms, pipeline_latency_ms=result.total_latency_ms,
        error_type=None, error_message_safe=None, requires_priority_review=requires_review,
    )


def _average(values: list[float | None]) -> float | None:
    known = [value for value in values if value is not None]
    return sum(known) / len(known) if known else None


def _token_total(values: list[int | None]) -> int | None:
    known = [value for value in values if value is not None]
    return sum(known) if known else None


def summarize(results: list[E2EQuestionResult]) -> E2ESummary:
    """Aggregate a non-empty batch without fabricating missing usage values."""
    if not results:
        raise evaluate.EvaluationError("Cannot summarize zero E2E question results")
    total = len(results)
    completed = [result for result in results if result.error_type is None]
    present_count = sum(result.expected_article_present for result in completed)
    cited_count = sum(result.expected_article_cited for result in completed)
    all_retrieved_count = sum(result.all_expected_articles_retrieved for result in completed)
    all_cited_count = sum(result.all_expected_articles_cited for result in completed)
    priority_review_count = sum(result.requires_priority_review for result in results)
    human_review_completed_count = sum(result.human_review.is_complete for result in results)
    recall = lambda k: sum(
        result.first_expected_rank is not None and result.first_expected_rank <= k for result in completed
    ) / total

    def _all_match_at(k: int) -> float:
        matches = 0
        for result in completed:
            expected = {evaluate.normalize_article_no(article) for article in result.expected_articles}
            retrieved = _normalized(result.retrieved_articles[:k])
            matches += expected.issubset(retrieved)
        return matches / total

    return E2ESummary(
        total_questions=total, completed_questions=len(completed), error_count=total - len(completed),
        expected_article_present_count=present_count, expected_article_present_rate=present_count / total,
        recall_at_1=recall(1), recall_at_3=recall(3), recall_at_5=recall(5),
        all_match_at_1=_all_match_at(1), all_match_at_3=_all_match_at(3), all_match_at_5=_all_match_at(5),
        all_expected_articles_retrieved_count=all_retrieved_count,
        all_expected_articles_retrieved_rate=all_retrieved_count / total,
        yeterli_count=sum(result.status == "YETERLI" for result in completed),
        yetersiz_count=sum(result.status == "YETERSIZ" for result in completed),
        answers_with_citations=sum(result.citation_count > 0 for result in completed),
        expected_article_cited_count=cited_count, expected_article_cited_rate=cited_count / total,
        all_expected_articles_cited_count=all_cited_count,
        all_expected_articles_cited_rate=all_cited_count / total,
        requires_priority_review_count=priority_review_count,
        requires_priority_review_rate=priority_review_count / total,
        human_review_completed_count=human_review_completed_count,
        human_review_pending_count=total - human_review_completed_count,
        average_retrieval_latency_ms=_average([result.retrieval_latency_ms for result in completed]),
        average_generation_latency_ms=_average([result.generation_latency_ms for result in completed]),
        average_pipeline_latency_ms=_average([result.pipeline_latency_ms for result in completed]),
        total_embedding_tokens=_token_total([result.embedding_tokens for result in completed]),
        total_generation_input_tokens=_token_total([result.generation_input_tokens for result in completed]),
        total_generation_output_tokens=_token_total([result.generation_output_tokens for result in completed]),
        total_generation_tokens=_token_total([result.generation_total_tokens for result in completed]),
    )


def evaluate_all(
    questions: list[evaluate.EvaluationQuestion], *, rag_runner: RAGRunner = rag.run_rag
) -> tuple[list[E2EQuestionResult], E2ESummary]:
    """Evaluate every question once; a supported pipeline error does not abort the batch."""
    results = [evaluate_question(question, rag_runner=rag_runner) for question in questions]
    return results, summarize(results)


def write_reports(report: E2EBatchReport, json_path: Path, csv_path: Path) -> None:
    """Write safe structured JSON and human-review-ready CSV artifacts."""
    json_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2), encoding="utf-8")
    fields = [
        "id", "question", "expected_articles", "expert_validated", "retrieved_articles",
        "retrieved_chunk_ids", "first_expected_rank", "expected_article_present",
        "all_expected_articles_retrieved", "status", "cited_articles", "expected_article_cited",
        "all_expected_articles_cited", "citation_count", "citation_labels_structurally_valid",
        "requires_priority_review", "answer", "retrieval_latency_ms", "generation_latency_ms",
        "pipeline_latency_ms", "embedding_tokens", "generation_input_tokens", "generation_output_tokens",
        "generation_total_tokens", "error_type", "error_message_safe", "legal_correctness", "completeness",
        "groundedness", "citation_relevance", "sufficiency_decision", "unsafe_overclaim", "reviewer_notes",
    ]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for result in report.results:
            row = asdict(result)
            review = row.pop("human_review")
            row.update(review)
            for name in ("expected_articles", "retrieved_articles", "retrieved_chunk_ids", "cited_articles"):
                row[name] = " | ".join("" if value is None else str(value) for value in row[name])
            writer.writerow({field: row.get(field) for field in fields})


def write_answer_review_csv(results: list[E2EQuestionResult], path: Path) -> None:
    """Write system-answer review rows while leaving every human score blank."""
    fields = [
        "id", "question", "expected_articles", "retrieved_articles", "first_expected_rank",
        "all_expected_articles_retrieved", "status", "cited_articles", "expected_article_cited",
        "all_expected_articles_cited", "requires_priority_review", "answer",
        "legal_correctness", "completeness", "groundedness", "citation_relevance",
        "sufficiency_decision", "unsafe_overclaim", "reviewer_notes",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for result in results:
            writer.writerow({
                "id": result.id, "question": result.question,
                "expected_articles": " | ".join(result.expected_articles),
                "retrieved_articles": " | ".join(article or "" for article in result.retrieved_articles),
                "first_expected_rank": result.first_expected_rank, "status": result.status,
                "all_expected_articles_retrieved": result.all_expected_articles_retrieved,
                "cited_articles": " | ".join(article or "" for article in result.cited_articles),
                "expected_article_cited": result.expected_article_cited,
                "all_expected_articles_cited": result.all_expected_articles_cited,
                "requires_priority_review": result.requires_priority_review, "answer": result.answer,
                "legal_correctness": "", "completeness": "", "groundedness": "",
                "citation_relevance": "", "sufficiency_decision": "", "unsafe_overclaim": "",
                "reviewer_notes": "",
            })


def summarize_extension_groups(
    extension_questions: list[object], results: list[E2EQuestionResult], attribute: str
) -> dict[str, E2ESummary]:
    """Summarize extension results by one validated categorical attribute."""
    by_id = {result.id: result for result in results}
    grouped: dict[str, list[E2EQuestionResult]] = {}
    for question in extension_questions:
        value = getattr(question, attribute)
        grouped.setdefault(value, []).append(by_id[getattr(question, "id")])
    return {name: summarize(group_results) for name, group_results in sorted(grouped.items())}


def priority_review_cases(results: list[E2EQuestionResult]) -> tuple[FailureCase, ...]:
    """Return safe compact diagnostics for every structural priority case."""
    return tuple(
        FailureCase(result.id, result.question, result.expected_articles, result.retrieved_articles,
                    result.status, result.cited_articles)
        for result in results
        if result.requires_priority_review
    )


def _sha256(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _real_evaluation_opt_in() -> bool:
    return bool(config.OPENAI_API_KEY) and os.getenv("RUN_OPENAI_INTEGRATION_TESTS") == "1"


def _pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def _print_report(report: E2EBatchReport, *, compare_frozen_m9a: bool = True) -> None:
    print("ID | expected | first rank | status | cited articles | expected cited | priority review")
    for result in report.results:
        print(f"{result.id} | {','.join(result.expected_articles)} | {result.first_expected_rank or '-'} | "
              f"{result.status or 'ERROR'} | {','.join(a or '?' for a in result.cited_articles) or '-'} | "
              f"{result.expected_article_cited} | {result.requires_priority_review}")
    summary = report.summary
    print(f"\nQuestions: {summary.total_questions} | Errors: {summary.error_count}")
    print(f"Expected article retrieval presence: {summary.expected_article_present_count}/{summary.total_questions} "
          f"({_pct(summary.expected_article_present_rate)})")
    print(f"YETERLI: {summary.yeterli_count} | YETERSIZ: {summary.yetersiz_count}")
    print(f"Expected article cited rate: {_pct(summary.expected_article_cited_rate)}")
    print(f"All expected articles cited rate: {_pct(summary.all_expected_articles_cited_rate)}")
    print(f"Structural priority-review rate: {_pct(summary.requires_priority_review_rate)}")
    print(f"Human/expert legal review completed: {summary.human_review_completed_count}/{summary.total_questions}")
    print(f"Human/expert legal review pending: {summary.human_review_pending_count}/{summary.total_questions}")
    print(f"Average latencies ms (retrieval/generation/pipeline): {summary.average_retrieval_latency_ms} / "
          f"{summary.average_generation_latency_ms} / {summary.average_pipeline_latency_ms}")
    print(f"Token totals (embedding/input/output/generation): {summary.total_embedding_tokens} / "
          f"{summary.total_generation_input_tokens} / {summary.total_generation_output_tokens} / "
          f"{summary.total_generation_tokens}")
    for k in (1, 3, 5):
        observed = getattr(summary, f"recall_at_{k}")
        if compare_frozen_m9a:
            state = "MATCH" if observed == FROZEN_RECALL[k] else "DRIFT"
            print(f"Recall@{k}: {_pct(observed)} (frozen {_pct(FROZEN_RECALL[k])}) [{state}]")
        else:
            print(f"Recall@{k}: {_pct(observed)}")
    print("ALL-match retrieval (every expected article present):")
    for k in (1, 3, 5):
        print(f"ALL-match@{k}: {_pct(getattr(summary, f'all_match_at_{k}'))}")


def main(argv: list[str] | None = None) -> None:
    """Run the explicitly gated, one-pass real baseline and write artifacts."""
    parser = argparse.ArgumentParser(description="Run a gated structural E2E benchmark")
    parser.add_argument(
        "--benchmark", choices=("m9a", "m9b"), default="m9a",
        help="m9a keeps the frozen 15-question default; m9b explicitly runs the combined 45-question benchmark",
    )
    args = parser.parse_args(argv)
    if not _real_evaluation_opt_in():
        print("Real E2E evaluation skipped: requires OPENAI_API_KEY and RUN_OPENAI_INTEGRATION_TESTS=1.")
        return
    import chromadb

    extension_questions: list[object] = []
    if args.benchmark == "m9b":
        from src import evaluation_dataset
        extension_questions = list(evaluation_dataset.load_extension_questions())
        questions = evaluation_dataset.load_m9b_benchmark()
        dataset_path_text = "tests/questions.json + evaluation/questions_m9b.json"
        dataset_hash = _sha256(DEFAULT_QUESTIONS_PATH) + "+" + _sha256(evaluation_dataset.M9B_EXTENSION_PATH)
        json_report, csv_report = M9B_JSON_REPORT, M9B_CSV_REPORT
    else:
        questions = evaluate.load_questions(DEFAULT_QUESTIONS_PATH)
        dataset_path_text = str(DEFAULT_QUESTIONS_PATH.relative_to(PROJECT_ROOT)).replace("\\", "/")
        dataset_hash = _sha256(DEFAULT_QUESTIONS_PATH)
        json_report, csv_report = DEFAULT_JSON_REPORT, DEFAULT_CSV_REPORT
    client = chromadb.PersistentClient(path=config.CHROMA_PATH)
    collection = client.get_collection(config.COLLECTION_NAME)
    count_before = collection.count()
    if count_before != 53:
        print(
            f"Real E2E evaluation aborted: collection count is {count_before}, expected 53.",
            file=sys.stderr,
        )
        return
    metric = retrieve.distance_metric(collection)
    results, summary = evaluate_all(questions)
    count_after = collection.count()
    metadata = RunMetadata(
        run_timestamp=datetime.now(timezone.utc).isoformat(), evaluation_question_count=len(questions),
        collection_name=config.COLLECTION_NAME, collection_count_before=count_before,
        collection_count_after=count_after, embedding_model=config.EMBEDDING_MODEL,
        llm_model=config.LLM_MODEL, top_k=config.TOP_K, distance_metric=metric,
        dataset_path=dataset_path_text, dataset_sha256=dataset_hash,
    )
    report = E2EBatchReport(metadata=metadata, summary=summary, results=tuple(results))
    write_reports(report, json_report, csv_report)
    if args.benchmark == "m9b":
        m9b_report = M9BProvisionalReport(
            metadata=metadata, summary=summary, m9a_subset_summary=summarize(results[:15]),
            case_type_breakdown=summarize_extension_groups(extension_questions, results, "case_type"),
            difficulty_breakdown=summarize_extension_groups(extension_questions, results, "difficulty"),
            failure_cases=priority_review_cases(results), results=tuple(results),
        )
        json_report.write_text(json.dumps(asdict(m9b_report), ensure_ascii=False, indent=2), encoding="utf-8")
        write_answer_review_csv(results, M9B_ANSWER_REVIEW)
    _print_report(report, compare_frozen_m9a=args.benchmark == "m9a")
    print(f"Collection count before/after: {count_before}/{count_after}")
    print(f"Reports: {json_report} | {csv_report}")
    if args.benchmark == "m9b":
        subset = summarize(results[:15])
        print("M9A subset drift checks:")
        for k in (1, 3, 5):
            observed = getattr(subset, f"recall_at_{k}")
            print(f"Recall@{k}: {_pct(observed)} [{'MATCH' if observed == FROZEN_RECALL[k] else 'DRIFT'}]")
    if count_before != 53 or count_after != 53:
        print("WARNING: collection count invariant (53) failed.", file=sys.stderr)


if __name__ == "__main__":
    main()
