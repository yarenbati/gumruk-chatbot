"""Offline validation tests for the frozen seed plus M9B extension workflow."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from src import evaluate, evaluate_e2e, evaluation_dataset

SEED_SHA256 = "a5aa901d6dfe65969142ed9a028024b93a777338ecab48124dd7f1b380034ba3"


def _extension_data() -> list[dict[str, object]]:
    return json.loads(evaluation_dataset.M9B_EXTENSION_PATH.read_text(encoding="utf-8"))


def _write(tmp_path: Path, data: object) -> Path:
    path = tmp_path / "questions.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


def _structural_result(qid: str) -> evaluate_e2e.E2EQuestionResult:
    return evaluate_e2e.E2EQuestionResult(
        id=qid, question="Soru?", expected_articles=("1",), expert_validated=False,
        retrieved_articles=("1",), retrieved_chunk_ids=("c-1",), expected_article_present=True,
        first_expected_rank=1, all_expected_articles_retrieved=True, status="YETERLI",
        insufficient_context=False, answer="Yanıt. [KAYNAK 1]", cited_articles=("1",),
        citation_count=1, citation_labels_structurally_valid=True, expected_article_cited=True,
        all_expected_articles_cited=True, embedding_tokens=None, generation_input_tokens=None,
        generation_output_tokens=None, generation_total_tokens=None, retrieval_latency_ms=1.0,
        generation_latency_ms=2.0, pipeline_latency_ms=3.0, error_type=None,
        error_message_safe=None, requires_priority_review=False,
    )


def test_frozen_seed_hash_unchanged() -> None:
    assert hashlib.sha256(evaluation_dataset.SEED_QUESTIONS_PATH.read_bytes()).hexdigest() == SEED_SHA256


def test_extension_shape_ids_and_combined_order() -> None:
    extension = evaluation_dataset.load_extension_questions()
    combined = evaluation_dataset.load_m9b_benchmark()
    assert len(extension) == 30 and len(combined) == 45
    assert [q.id for q in extension] == list(evaluation_dataset.EXPECTED_EXTENSION_IDS)
    assert [q.id for q in combined] == [f"q{i:03d}" for i in range(1, 46)]
    assert len({q.id for q in combined}) == 45


def test_extension_required_values_and_article_coverage() -> None:
    extension = evaluation_dataset.load_extension_questions()
    assert all(q.question.strip() and q.expected_articles for q in extension)
    assert all(q.case_type in evaluation_dataset.ALLOWED_CASE_TYPES for q in extension)
    assert all(q.difficulty in evaluation_dataset.ALLOWED_DIFFICULTIES for q in extension)
    assert all(q.source_verified is True and q.expert_validated is False for q in extension)
    articles = {evaluate.normalize_article_no(article) for q in extension for article in q.expected_articles}
    assert len(articles) >= 20 and "42/a" in articles and "43/c" in articles


def test_extension_target_distributions_are_exact() -> None:
    extension = evaluation_dataset.load_extension_questions()
    case_counts = {name: sum(q.case_type == name for q in extension) for name in evaluation_dataset.ALLOWED_CASE_TYPES}
    assert case_counts == {
        "paraphrase": 8, "exception_condition": 8, "multi_part": 6,
        "long_tail": 4, "ambiguity_resistant": 4,
    }
    assert {level: sum(q.difficulty == level for q in extension) for level in evaluation_dataset.ALLOWED_DIFFICULTIES} == {
        "easy": 5, "medium": 12, "hard": 13,
    }


def test_no_duplicate_ids_or_normalized_questions() -> None:
    combined = evaluation_dataset.load_m9b_benchmark()
    normalized = [evaluation_dataset.normalize_question_text(q.question) for q in combined]
    assert len({q.id for q in combined}) == len(combined)
    assert len(set(normalized)) == len(normalized)


def test_duplicate_id_across_files_rejected(tmp_path: Path) -> None:
    duplicate_seed = [{"id": "q016", "question": "Başka soru?", "expected_articles": ["1"], "expert_validated": False}]
    with pytest.raises(evaluate.EvaluationError, match="Duplicate question ID"):
        evaluation_dataset.load_question_sets([evaluation_dataset.M9B_EXTENSION_PATH, _write(tmp_path, duplicate_seed)])


@pytest.mark.parametrize(("field", "value", "message"), [
    ("case_type", "unknown", "invalid case_type"),
    ("difficulty", "impossible", "invalid difficulty"),
    ("source_verified", False, "source_verified=true"),
    ("expert_validated", True, "expert_validated=false"),
])
def test_extension_validation_rejects_invalid_metadata(tmp_path: Path, field: str, value: object, message: str) -> None:
    data = _extension_data()
    data[0][field] = value
    with pytest.raises(evaluate.EvaluationError, match=message):
        evaluation_dataset.load_extension_questions(_write(tmp_path, data))


def test_duplicate_normalized_extension_question_rejected(tmp_path: Path) -> None:
    data = _extension_data()
    data[1]["question"] = "  " + str(data[0]["question"]) + "  "
    with pytest.raises(evaluate.EvaluationError, match="Duplicate normalized"):
        evaluation_dataset.load_extension_questions(_write(tmp_path, data))


def test_question_review_template_is_pending_and_blank(tmp_path: Path) -> None:
    path = tmp_path / "question-review.csv"
    evaluation_dataset.write_question_review_csv(evaluation_dataset.load_extension_questions(), path)
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig")))
    blank = ("question_clear", "question_natural", "expected_articles_correct",
             "answerable_from_current_corpus", "ambiguous", "reviewer_notes")
    assert len(rows) == 30 and all(row["review_status"] == "pending" for row in rows)
    assert all(not row[field] for row in rows for field in blank)


def test_answer_review_template_has_45_blank_human_scores(tmp_path: Path) -> None:
    path = tmp_path / "answer-review.csv"
    results = [replace(_structural_result(q.id), question=q.question, expected_articles=q.expected_articles,
                       expert_validated=q.expert_validated) for q in evaluation_dataset.load_m9b_benchmark()]
    evaluate_e2e.write_answer_review_csv(results, path)
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig")))
    human = ("legal_correctness", "completeness", "groundedness", "citation_relevance",
             "sufficiency_decision", "unsafe_overclaim", "reviewer_notes")
    assert len(rows) == 45 and all(not row[field] for row in rows for field in human)
    assert all(result.expert_validated is False for result in results)


def test_m9a_default_remains_15_and_explicit_m9b_is_45() -> None:
    assert len(evaluate.load_questions()) == 15
    assert len(evaluation_dataset.load_m9b_benchmark()) == 45


def test_frozen_m9a_any_recall_values_remain_unchanged() -> None:
    assert evaluate_e2e.FROZEN_RECALL == {1: 12 / 15, 3: 13 / 15, 5: 14 / 15}


def test_article_normalization_is_the_existing_contract() -> None:
    extension = evaluation_dataset.load_extension_questions()
    q038 = next(q for q in extension if q.id == "q038")
    assert q038.normalized_expected_articles == frozenset({evaluate.normalize_article_no("42-a")})
