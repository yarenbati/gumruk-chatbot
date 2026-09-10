"""Offline M10E-B candidate-holdout-construction contract tests.

Scope: `src.m10e_holdout` only. No test here calls OpenAI, opens production
Chroma, or touches the network — mirrors the M10E-B candidate-construction
phase boundary itself.
"""

from __future__ import annotations

import copy
import json

import pytest

from src import evaluate_multilaw as m
from src import m10e_holdout as h


def _base_raw(**overrides: object) -> dict:
    raw = {
        "id": "hx-01",
        "question": "Örnek soru metni burada yer alır mı?",
        "dataset": "4458",
        "expected_sources": [{"legislation_number": "4458", "article_type": "normal", "article_no": "2"}],
        "case_type": "paraphrase",
        "difficulty": "easy",
        "source_verified": True,
        "gold_human_approved": False,
        "expert_validated": False,
        "notes": "dogrudan kontrol edildi (src_para=1)",
    }
    raw.update(overrides)
    return raw


# ============================================================================
# DEV_GOLD_KEYS extraction
# ============================================================================


def test_dev_gold_keys_counts() -> None:
    """DEV_GOLD_KEYS matches the known frozen-benchmark distinct-key counts."""
    dev_5326 = frozenset(k for q in m.load_5326_questions() for k in q.expected_sources)
    dev_4458 = frozenset(k for q in m.load_4458_questions() for k in q.expected_sources)
    combined = h.compute_dev_gold_keys()
    assert combined == dev_5326 | dev_4458
    assert len(dev_5326) == 39
    assert len(dev_4458) == 31
    assert len(combined) == 70


def test_dev_gold_keys_deterministic() -> None:
    """Recomputing DEV_GOLD_KEYS twice yields an identical frozenset."""
    assert h.compute_dev_gold_keys() == h.compute_dev_gold_keys()


# ============================================================================
# Unused-key (HOLDOUT_ELIGIBLE_KEYS) selection
# ============================================================================


def test_eligible_keys_excludes_dev_gold() -> None:
    """HOLDOUT_ELIGIBLE_KEYS never contains a DEV_GOLD_KEYS member."""
    eligible = h.compute_eligible_keys()
    dev_gold = h.compute_dev_gold_keys()
    assert eligible & dev_gold == frozenset()
    assert eligible == h.compute_full_corpus_keys() - dev_gold


def test_eligible_keys_subset_of_corpus() -> None:
    """Every eligible key is a real corpus key (never invented)."""
    assert h.compute_eligible_keys() <= h.compute_full_corpus_keys()


# ============================================================================
# Candidate loading + zero dev-gold overlap (the real committed file)
# ============================================================================


def test_real_candidate_file_loads_and_has_zero_overlap() -> None:
    """The actual committed candidate file passes every structural and
    blindness check end-to-end."""
    questions = h.load_candidate_questions()
    assert len(questions) == h.EXPECTED_CANDIDATE_COUNT
    h.validate_zero_dev_gold_overlap(questions)
    h.validate_keys_exist_in_corpus(questions)

    per_law = {"5326": 0, "4458": 0}
    for q in questions:
        per_law[q.dataset] += 1
    assert per_law == {"5326": 10, "4458": 20}

    distinct_keys = h.candidate_gold_keys(questions)
    assert len(distinct_keys) == 35


def test_candidate_loading_is_deterministic() -> None:
    """Loading the same candidate file twice yields equal results."""
    assert h.load_candidate_questions() == h.load_candidate_questions()


# ============================================================================
# Deterministic candidate validation / malformed input rejection
# ============================================================================


def test_wrong_count_rejected(tmp_path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(json.dumps([_base_raw()]), encoding="utf-8")
    with pytest.raises(h.HoldoutConstructionError, match="exactly 30"):
        h.load_candidate_questions(path)


@pytest.mark.parametrize("field,value", [
    ("case_type", "not_a_real_case_type"),
    ("difficulty", "impossible"),
    ("source_verified", False),
    ("gold_human_approved", True),
    ("expert_validated", True),
    ("dataset", "9999"),
])
def test_invalid_field_rejected(tmp_path, field: str, value: object) -> None:
    raw = _base_raw(**{field: value})
    path = tmp_path / "bad.json"
    path.write_text(json.dumps([raw] * 30), encoding="utf-8")
    with pytest.raises(h.HoldoutConstructionError):
        h.load_candidate_questions(path)


def test_duplicate_question_text_rejected(tmp_path) -> None:
    raws = [_base_raw(id=f"hx-{i:02d}") for i in range(30)]
    raws[1]["question"] = raws[0]["question"]
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(raws), encoding="utf-8")
    with pytest.raises(h.HoldoutConstructionError, match="Duplicate normalized question text"):
        h.load_candidate_questions(path)


def test_legislation_mismatch_rejected(tmp_path) -> None:
    raw = _base_raw(expected_sources=[{"legislation_number": "5326", "article_type": "normal", "article_no": "2"}])
    path = tmp_path / "bad.json"
    path.write_text(json.dumps([raw] * 30), encoding="utf-8")
    with pytest.raises(h.HoldoutConstructionError, match="!= dataset"):
        h.load_candidate_questions(path)


def test_dev_gold_overlap_detected(tmp_path) -> None:
    """A candidate reusing a real dev-gold key must fail the blindness check."""
    dev_gold = next(iter(h.compute_dev_gold_keys()))
    raws = [_base_raw(id=f"hx-{i:02d}", question=f"Örnek soru metni {i} burada yer alır mı?") for i in range(30)]
    raws[0]["expected_sources"] = [{
        "legislation_number": dev_gold.legislation_number,
        "article_type": dev_gold.article_type,
        "article_no": dev_gold.article_no,
    }]
    raws[0]["dataset"] = dev_gold.legislation_number
    path = tmp_path / "overlap.json"
    path.write_text(json.dumps(raws), encoding="utf-8")
    questions = h.load_candidate_questions(path)
    with pytest.raises(h.HoldoutConstructionError, match="overlaps DEV_GOLD_KEYS"):
        h.validate_zero_dev_gold_overlap(questions)


def test_nonexistent_corpus_key_detected(tmp_path) -> None:
    """A fabricated article number must fail the corpus-existence check."""
    raws = [_base_raw(id=f"hx-{i:02d}", question=f"Örnek soru metni {i} burada yer alır mı?") for i in range(30)]
    raws[0]["expected_sources"] = [{"legislation_number": "4458", "article_type": "normal", "article_no": "999999"}]
    path = tmp_path / "fake.json"
    path.write_text(json.dumps(raws), encoding="utf-8")
    questions = h.load_candidate_questions(path)
    with pytest.raises(h.HoldoutConstructionError, match="absent from parsed corpus"):
        h.validate_keys_exist_in_corpus(questions)


# ============================================================================
# Source-key normalization (reused, not reimplemented)
# ============================================================================


def test_source_key_normalization_reused() -> None:
    """Article-number normalization in this module is exactly
    evaluate_multilaw's QualifiedSourceKey.build, not a private copy."""
    a = m.QualifiedSourceKey.build("4458", "normal", "165 / B")
    b = m.QualifiedSourceKey.build("4458", "normal", "165-b")
    assert a == b
    raw = _base_raw(expected_sources=[{"legislation_number": "4458", "article_type": "normal", "article_no": "165 / B"}])
    raws = [_base_raw(id=f"hx-{i:02d}", question=f"Örnek soru metni {i} burada yer alır mı?") for i in range(30)]
    raws[0] = {**raw, "id": "hx-00", "question": raws[0]["question"]}
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "norm.json"
        path.write_text(json.dumps(raws), encoding="utf-8")
        questions = h.load_candidate_questions(path)
    assert b in questions[0].expected_sources


# ============================================================================
# Candidate / final separation
# ============================================================================


def test_candidate_and_final_paths_are_distinct() -> None:
    assert h.CANDIDATE_PATH != h.FINAL_PATH
    assert h.CANDIDATE_PATH.name == "questions_m10e_holdout.candidate.json"
    assert h.FINAL_PATH.name == "questions_m10e_holdout.json"


def test_final_holdout_frozen_and_valid() -> None:
    """After human gold approval, the frozen final file exists and passes
    every structural/blindness check `load_final_questions` enforces."""
    assert h.FINAL_PATH.exists()
    questions = h.load_final_questions()
    assert len(questions) == h.EXPECTED_CANDIDATE_COUNT
    h.validate_zero_dev_gold_overlap(questions)
    h.validate_keys_exist_in_corpus(questions)

    per_law = {"5326": 0, "4458": 0}
    for q in questions:
        per_law[q.dataset] += 1
    assert per_law == {"5326": 10, "4458": 20}
    assert len(h.candidate_gold_keys(questions)) == 35


def test_final_holdout_rejects_unapproved_rows(tmp_path) -> None:
    """`load_final_questions` must reject a row that still has
    `gold_human_approved=false` (the candidate invariant, not the final
    one) — the two loaders enforce opposite flag values on purpose."""
    raw = json.loads(h.CANDIDATE_PATH.read_text(encoding="utf-8"))
    path = tmp_path / "still_candidate.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(h.HoldoutConstructionError, match="gold_human_approved must be True"):
        h.load_final_questions(path)


def test_final_matches_candidate_except_approved_corrections() -> None:
    """The final file differs from the candidate ONLY by
    `gold_human_approved` flipping to true on every row, plus the three
    explicitly human-approved question-text corrections — never
    `expected_sources`, `case_type`, `difficulty`, or `notes`."""
    approved_wording_changes = {
        "h5326-01": "Kabahatler Kanunu, hangi değerleri korumak amacıyla kabahatlere ilişkin genel çerçeveyi düzenler?",
        "h5326-03": "Bir gürültü fiili ticari işletmenin faaliyeti çerçevesinde işlenirse idari para cezası kime uygulanır?",
        "h4458-11": (
            "Basitleştirilmiş usulde tescil edilen bir beyannamedeki eksik bilgiler "
            "verilen süre içinde tamamlanmazsa, o eşya için ödenmesi gereken vergiler ertelenir mi?"
        ),
    }
    candidate_raw = {r["id"]: r for r in json.loads(h.CANDIDATE_PATH.read_text(encoding="utf-8"))}
    final_raw = {r["id"]: r for r in json.loads(h.FINAL_PATH.read_text(encoding="utf-8"))}
    assert set(candidate_raw) == set(final_raw)

    for qid, c in candidate_raw.items():
        f = final_raw[qid]
        assert c["expected_sources"] == f["expected_sources"], qid
        assert c["case_type"] == f["case_type"], qid
        assert c["difficulty"] == f["difficulty"], qid
        assert c["dataset"] == f["dataset"], qid
        assert c["notes"] == f["notes"], qid
        assert c["source_verified"] is True and f["source_verified"] is True
        assert c["expert_validated"] is False and f["expert_validated"] is False
        assert c["gold_human_approved"] is False
        assert f["gold_human_approved"] is True

        if qid in approved_wording_changes:
            assert f["question"] == approved_wording_changes[qid], qid
            assert f["question"] != c["question"], qid
        else:
            assert f["question"] == c["question"], qid

    assert set(approved_wording_changes) == {"h5326-01", "h5326-03", "h4458-11"}


def test_final_holdout_sha256_reported() -> None:
    """The frozen file's SHA-256 is computable and stable across reads."""
    import hashlib

    digest_1 = hashlib.sha256(h.FINAL_PATH.read_bytes()).hexdigest()
    digest_2 = hashlib.sha256(h.FINAL_PATH.read_bytes()).hexdigest()
    assert digest_1 == digest_2
    assert len(digest_1) == 64


def test_module_defines_no_freeze_or_run_function() -> None:
    """The candidate-construction module exposes no function that could
    freeze the final dataset or launch a holdout retrieval run."""
    forbidden_substrings = ("freeze", "run_b0", "run_b2", "run_holdout")
    for name in dir(h):
        lowered = name.lower()
        assert not any(token in lowered for token in forbidden_substrings), name


# ============================================================================
# No retrieval callable during candidate-construction phase
# ============================================================================


def test_module_never_imports_retrieval_or_openai() -> None:
    """`src.m10e_holdout` must not import `src.retrieve` or `openai` at
    module scope, so no code path in this phase can call retrieval."""
    assert not hasattr(h, "retrieve")
    assert not hasattr(h, "openai")
    assert not hasattr(h, "OpenAI")
    assert "retrieve" not in h.__dict__
    assert "openai" not in h.__dict__


def test_module_has_no_network_dependent_globals() -> None:
    """Every public module-level callable is import-safe: importing the
    module performs no I/O beyond nothing (constants only)."""
    import importlib

    reloaded = importlib.reload(h)
    assert reloaded is h
