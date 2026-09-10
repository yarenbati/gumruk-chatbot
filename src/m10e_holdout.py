"""
M10E-B blind holdout construction — CANDIDATE + POST-APPROVAL LOADING ONLY
(see task boundary in the M10E-B milestone brief).

Scope: build DEV_GOLD_KEYS, derive HOLDOUT_ELIGIBLE_KEYS, strictly validate
the pending human-review candidate file
(evaluation/questions_m10e_holdout.candidate.json), and — once a later,
separate human-approval step has produced it — strictly validate the frozen
final file (evaluation/questions_m10e_holdout.json). This module never
WRITES either file itself (freezing the final file is a human-approval-
driven step performed outside this module) and never calls retrieval, never
calls OpenAI, and never opens production Chroma. Running B0/B2 and
computing holdout metrics remain separate, LATER milestone steps and are
intentionally out of scope here. `src.retrieve` and `openai` are
deliberately never imported by this module.

DEV_GOLD_KEYS is the union of every QualifiedSourceKey used as gold in the
frozen 75-question M10D/M10E-A development benchmark (45 x 5326 seed+
extension + 30 x 4458), computed by reusing `src.evaluate_multilaw`'s
existing loaders — never by re-parsing `tests/questions.json`,
`evaluation/questions_m9b.json`, or `evaluation/questions_4458.json` here.

HOLDOUT_ELIGIBLE_KEYS is every real Article-level QualifiedSourceKey in the
current 5326+4458 corpus (via the existing `src.chunk` parser / the
persisted 5326 articles.json — never a competing parser) minus
DEV_GOLD_KEYS.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src import chunk as chunk_module
from src import evaluate_multilaw as m
from src import evaluation_dataset as ed

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CANDIDATE_PATH = PROJECT_ROOT / "evaluation" / "questions_m10e_holdout.candidate.json"
FINAL_PATH = PROJECT_ROOT / "evaluation" / "questions_m10e_holdout.json"
ARTICLES_5326_PATH = PROJECT_ROOT / "data" / "processed" / "5326-kabahatler-kanunu.articles.json"
PARAGRAPHS_4458_PATH = PROJECT_ROOT / "data" / "processed" / "4458-gumruk-kanunu.paragraphs.json"

EXPECTED_CANDIDATE_COUNT = 30
ALLOWED_DATASETS = frozenset({"5326", "4458"})
ALLOWED_CASE_TYPES = ed.ALLOWED_CASE_TYPES
ALLOWED_DIFFICULTIES = ed.ALLOWED_DIFFICULTIES


class HoldoutConstructionError(RuntimeError):
    """Raised for malformed candidate holdout input, a DEV_GOLD_KEYS
    overlap, or a QualifiedSourceKey absent from the real parsed corpus.
    Never silently accepts contaminated or unverifiable ground truth.
    """


@dataclass(frozen=True)
class HoldoutCandidateQuestion:
    """One validated, source-verified but not yet human-approved M10E-B
    holdout candidate question."""

    id: str
    question: str
    dataset: str
    expected_sources: frozenset[m.QualifiedSourceKey]
    case_type: str
    difficulty: str
    notes: str


# ============================================================================
# DEV_GOLD_KEYS / HOLDOUT_ELIGIBLE_KEYS (§3-§4 of the M10E-B brief)
# ============================================================================


def compute_dev_gold_keys() -> frozenset[m.QualifiedSourceKey]:
    """Every QualifiedSourceKey used as gold in the frozen 75-question
    development benchmark, reusing the existing M10D loaders."""
    keys: set[m.QualifiedSourceKey] = set()
    for q in m.load_5326_questions():
        keys |= q.expected_sources
    for q in m.load_4458_questions():
        keys |= q.expected_sources
    return frozenset(keys)


def compute_full_corpus_keys() -> frozenset[m.QualifiedSourceKey]:
    """Every real Article-level QualifiedSourceKey in the current 5326+4458
    corpus, via the existing parser / persisted articles.json. Returns just
    the 5326 subset if the ignored 4458 raw paragraphs artifact is absent
    (mirrors `evaluate_multilaw._real_4458_qualified_keys`'s skip pattern)."""
    keys: set[m.QualifiedSourceKey] = set()
    articles_5326 = json.loads(ARTICLES_5326_PATH.read_text(encoding="utf-8"))
    for a in articles_5326["articles"]:
        keys.add(m.QualifiedSourceKey.build(a["legislation_number"], a["article_type"], a["article_no"]))
    if PARAGRAPHS_4458_PATH.exists():
        _, articles_4458 = chunk_module._load_and_parse_articles(PARAGRAPHS_4458_PATH)
        for a in articles_4458:
            keys.add(m.QualifiedSourceKey.build(a.legislation_number, a.article_type, a.article_no))
    return frozenset(keys)


def compute_eligible_keys() -> frozenset[m.QualifiedSourceKey]:
    """HOLDOUT_ELIGIBLE_KEYS = full corpus Article keys - DEV_GOLD_KEYS."""
    return compute_full_corpus_keys() - compute_dev_gold_keys()


# ============================================================================
# Candidate file loading/validation (§7-§8)
# ============================================================================


def _validate_raw_question(
    raw: Any, *, index: int, expected_gold_human_approved: bool = False
) -> HoldoutCandidateQuestion:
    if not isinstance(raw, dict):
        raise HoldoutConstructionError(f"Candidate at index {index} must be a JSON object")

    qid = raw.get("id")
    if not isinstance(qid, str) or not qid.strip():
        raise HoldoutConstructionError(f"Candidate at index {index} has a missing/empty 'id'")

    question_text = raw.get("question")
    if not isinstance(question_text, str) or not question_text.strip():
        raise HoldoutConstructionError(f"{qid}: missing/empty 'question'")

    dataset = raw.get("dataset")
    if dataset not in ALLOWED_DATASETS:
        raise HoldoutConstructionError(f"{qid}: invalid dataset {dataset!r}")

    if raw.get("case_type") not in ALLOWED_CASE_TYPES:
        raise HoldoutConstructionError(f"{qid}: invalid case_type {raw.get('case_type')!r}")
    if raw.get("difficulty") not in ALLOWED_DIFFICULTIES:
        raise HoldoutConstructionError(f"{qid}: invalid difficulty {raw.get('difficulty')!r}")
    if raw.get("source_verified") is not True:
        raise HoldoutConstructionError(f"{qid}: source_verified must be true")
    if raw.get("gold_human_approved") is not expected_gold_human_approved:
        raise HoldoutConstructionError(
            f"{qid}: gold_human_approved must be {expected_gold_human_approved!r} at this stage"
        )
    if raw.get("expert_validated") is not False:
        raise HoldoutConstructionError(f"{qid}: expert_validated must remain false")
    notes = raw.get("notes")
    if not isinstance(notes, str) or not notes.strip():
        raise HoldoutConstructionError(f"{qid}: missing/empty notes")

    sources = raw.get("expected_sources")
    if not isinstance(sources, list) or not sources:
        raise HoldoutConstructionError(f"{qid}: missing/empty expected_sources")

    seen: set[m.QualifiedSourceKey] = set()
    keys: list[m.QualifiedSourceKey] = []
    for source in sources:
        if not isinstance(source, dict):
            raise HoldoutConstructionError(f"{qid}: expected_sources entries must be objects")
        leg = source.get("legislation_number")
        if leg != dataset:
            raise HoldoutConstructionError(f"{qid}: expected_source legislation_number {leg!r} != dataset {dataset!r}")
        key = m.QualifiedSourceKey.build(leg, source.get("article_type"), source.get("article_no"))
        if key in seen:
            raise HoldoutConstructionError(f"{qid}: duplicate QualifiedSourceKey within one question: {key}")
        seen.add(key)
        keys.append(key)

    return HoldoutCandidateQuestion(
        id=qid, question=question_text, dataset=dataset, expected_sources=frozenset(keys),
        case_type=raw["case_type"], difficulty=raw["difficulty"], notes=notes,
    )


def _load_questions(
    path: str | Path, *, expected_gold_human_approved: bool, label: str
) -> list[HoldoutCandidateQuestion]:
    raw_questions = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw_questions, list):
        raise HoldoutConstructionError(f"Expected a JSON list of questions in {path}")
    if len(raw_questions) != EXPECTED_CANDIDATE_COUNT:
        raise HoldoutConstructionError(
            f"{label} holdout must contain exactly {EXPECTED_CANDIDATE_COUNT} questions, got {len(raw_questions)}"
        )

    questions: list[HoldoutCandidateQuestion] = []
    ids: set[str] = set()
    normalized_texts: set[str] = set()
    for index, raw in enumerate(raw_questions):
        q = _validate_raw_question(raw, index=index, expected_gold_human_approved=expected_gold_human_approved)
        if q.id in ids:
            raise HoldoutConstructionError(f"Duplicate {label.lower()} ID: {q.id}")
        ids.add(q.id)
        normalized_text = ed.normalize_question_text(q.question)
        if normalized_text in normalized_texts:
            raise HoldoutConstructionError(f"Duplicate normalized question text at {q.id!r}")
        normalized_texts.add(normalized_text)
        questions.append(q)
    return questions


def load_candidate_questions(path: str | Path = CANDIDATE_PATH) -> list[HoldoutCandidateQuestion]:
    """Strictly load+validate the pending candidate holdout file
    (`gold_human_approved` must be `false` on every row). Never reads or
    writes `FINAL_PATH` here — the candidate and final files are
    deliberately separate artifacts at this milestone phase."""
    return _load_questions(path, expected_gold_human_approved=False, label="Candidate")


def load_final_questions(path: str | Path = FINAL_PATH) -> list[HoldoutCandidateQuestion]:
    """Strictly load+validate the FROZEN final holdout file (`gold_human_
    approved` must be `true` on every row, `expert_validated` remains
    `false` unless a real legal/customs expert later reviews it). Only
    meaningful after the human-approval step has created `FINAL_PATH` —
    never reads `CANDIDATE_PATH`."""
    return _load_questions(path, expected_gold_human_approved=True, label="Final")


def candidate_gold_keys(questions: list[HoldoutCandidateQuestion]) -> frozenset[m.QualifiedSourceKey]:
    keys: set[m.QualifiedSourceKey] = set()
    for q in questions:
        keys |= q.expected_sources
    return frozenset(keys)


def validate_zero_dev_gold_overlap(questions: list[HoldoutCandidateQuestion]) -> None:
    """Raise if any candidate gold key was already used as dev-benchmark
    gold (§10 blindness rule: the holdout must not reuse dev gold keys)."""
    overlap = candidate_gold_keys(questions) & compute_dev_gold_keys()
    if overlap:
        raise HoldoutConstructionError(f"Candidate overlaps DEV_GOLD_KEYS: {sorted(str(k) for k in overlap)}")


def validate_keys_exist_in_corpus(questions: list[HoldoutCandidateQuestion]) -> None:
    """Raise if any candidate gold QualifiedSourceKey does not exist in the
    real parsed corpus (never trust an unverifiable citation)."""
    corpus = compute_full_corpus_keys()
    missing = candidate_gold_keys(questions) - corpus
    if missing:
        raise HoldoutConstructionError(f"Candidate keys absent from parsed corpus: {sorted(str(k) for k in missing)}")
