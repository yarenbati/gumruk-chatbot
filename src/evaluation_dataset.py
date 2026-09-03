"""M9B evaluation-dataset validation and human-review artifact helpers."""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from src import evaluate

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SEED_QUESTIONS_PATH = evaluate.DEFAULT_QUESTIONS_PATH
M9B_EXTENSION_PATH = PROJECT_ROOT / "evaluation" / "questions_m9b.json"
ALLOWED_CASE_TYPES = frozenset({
    "paraphrase", "exception_condition", "multi_part", "long_tail", "ambiguity_resistant"
})
ALLOWED_DIFFICULTIES = frozenset({"easy", "medium", "hard"})
EXPECTED_EXTENSION_IDS = tuple(f"q{number:03d}" for number in range(16, 46))


@dataclass(frozen=True)
class ExtensionQuestion(evaluate.EvaluationQuestion):
    """One validated, source-verified but not expert-validated M9B question."""

    case_type: str = ""
    difficulty: str = ""
    source_verified: bool = False
    notes: str = ""


def normalize_question_text(text: str) -> str:
    """Normalize whitespace and case for deterministic exact-duplicate checks."""
    return re.sub(r"\s+", " ", text.strip().casefold())


def _load_raw(path: str | Path) -> list[Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise evaluate.EvaluationError(f"Expected a JSON list of questions in {path}")
    return data


def load_extension_questions(path: str | Path = M9B_EXTENSION_PATH) -> list[ExtensionQuestion]:
    """Load and strictly validate the 30-record q016-q045 M9B extension."""
    raw_questions = _load_raw(path)
    if len(raw_questions) != 30:
        raise evaluate.EvaluationError(f"M9B extension must contain exactly 30 questions, got {len(raw_questions)}")

    questions: list[ExtensionQuestion] = []
    normalized_texts: set[str] = set()
    for index, raw in enumerate(raw_questions):
        base = evaluate._validate_and_build_question(raw, index=index)
        if base.id != EXPECTED_EXTENSION_IDS[index]:
            raise evaluate.EvaluationError(
                f"M9B extension IDs must be q016..q045 in order; index {index} has {base.id!r}"
            )
        case_type = raw.get("case_type")
        if case_type not in ALLOWED_CASE_TYPES:
            raise evaluate.EvaluationError(f"Question {base.id!r} has invalid case_type {case_type!r}")
        difficulty = raw.get("difficulty")
        if difficulty not in ALLOWED_DIFFICULTIES:
            raise evaluate.EvaluationError(f"Question {base.id!r} has invalid difficulty {difficulty!r}")
        source_verified = raw.get("source_verified")
        if source_verified is not True:
            raise evaluate.EvaluationError(f"Question {base.id!r} must have source_verified=true")
        if base.expert_validated is not False:
            raise evaluate.EvaluationError(f"Question {base.id!r} must remain expert_validated=false")
        notes = raw.get("notes")
        if not isinstance(notes, str) or not notes.strip():
            raise evaluate.EvaluationError(f"Question {base.id!r} has missing/empty notes")
        normalized_text = normalize_question_text(base.question)
        if normalized_text in normalized_texts:
            raise evaluate.EvaluationError(f"Duplicate normalized question text at {base.id!r}")
        normalized_texts.add(normalized_text)
        questions.append(ExtensionQuestion(**base.__dict__, case_type=case_type, difficulty=difficulty,
                                           source_verified=True, notes=notes))
    return questions


def load_question_sets(paths: Sequence[str | Path]) -> list[evaluate.EvaluationQuestion]:
    """Load datasets in explicit path order and reject duplicate IDs/text across files."""
    combined: list[evaluate.EvaluationQuestion] = []
    ids: set[str] = set()
    normalized_texts: set[str] = set()
    for path in paths:
        raw = _load_raw(path)
        is_extension = bool(raw) and all(isinstance(item, dict) and "case_type" in item for item in raw)
        loaded: list[evaluate.EvaluationQuestion]
        loaded = list(load_extension_questions(path)) if is_extension else evaluate.load_questions(path)
        for question in loaded:
            if question.id in ids:
                raise evaluate.EvaluationError(f"Duplicate question ID across datasets: {question.id}")
            normalized_text = normalize_question_text(question.question)
            if normalized_text in normalized_texts:
                raise evaluate.EvaluationError(f"Duplicate normalized question text across datasets: {question.id}")
            ids.add(question.id)
            normalized_texts.add(normalized_text)
            combined.append(question)
    if not combined:
        raise evaluate.EvaluationError("Cannot load zero combined questions")
    return combined


def load_m9b_benchmark() -> list[evaluate.EvaluationQuestion]:
    """Load frozen seed first and M9B extension second, yielding q001..q045."""
    return load_question_sets([SEED_QUESTIONS_PATH, M9B_EXTENSION_PATH])


def write_question_review_csv(questions: Sequence[ExtensionQuestion], path: str | Path) -> None:
    """Write a pending question/ground-truth review template without auto-approval."""
    fields = [
        "id", "question", "expected_articles", "case_type", "difficulty", "source_verified",
        "expert_validated", "question_clear", "question_natural", "expected_articles_correct",
        "answerable_from_current_corpus", "ambiguous", "review_status", "reviewer_notes",
    ]
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for question in questions:
            writer.writerow({
                "id": question.id, "question": question.question,
                "expected_articles": " | ".join(question.expected_articles),
                "case_type": question.case_type, "difficulty": question.difficulty,
                "source_verified": question.source_verified, "expert_validated": question.expert_validated,
                "question_clear": "", "question_natural": "", "expected_articles_correct": "",
                "answerable_from_current_corpus": "", "ambiguous": "", "review_status": "pending",
                "reviewer_notes": "",
            })
