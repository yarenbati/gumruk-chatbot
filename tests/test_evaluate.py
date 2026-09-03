"""Tests for src/evaluate.py (M5B retrieval evaluation / Recall@K).

All tests are self-contained: they never call OpenAI, never require
`OPENAI_API_KEY`, and never make network calls. Most tests exercise pure
metric math (`evaluate_question` / `summarize` / `normalize_article_no`)
against synthetic ranked-article lists - no retrieval, no Chroma, no
OpenAI. `tests/questions.json` is only ever READ here (via `load_questions`)
to prove the loader does not modify it - never used to compute or assert
any Recall@K number in this file (that belongs to the real evaluation CLI
run, a separate manual/opt-in step - see src/evaluate.py's module docstring).

One end-to-end wiring test (`test_evaluate_all_calls_retrieve_exactly_once_per_question`)
uses a fake OpenAI client (mirroring tests/test_embed.py's `_FakeClient`) and
a real, local, tmp_path-rooted Chroma collection - never the project's real
`chroma/` directory - to prove `evaluate_all` calls `retrieve()` exactly once
per question rather than once per K cutoff.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from src import config, evaluate, index
from src.chunk import Chunk
from src.embed import EmbeddingResult

# ============================================================================
# Fixture helpers
# ============================================================================


def _q(
    qid: str = "q1",
    question: str = "Test question?",
    expected: tuple[str, ...] = ("10",),
) -> evaluate.EvaluationQuestion:
    normalized = frozenset(evaluate.normalize_article_no(a) for a in expected)
    return evaluate.EvaluationQuestion(
        id=qid,
        question=question,
        expected_articles=tuple(expected),
        normalized_expected_articles=normalized,
    )


def _write_questions(tmp_path: Path, data: Any) -> Path:
    path = tmp_path / "questions.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


# ============================================================================
# 1-3: Recall@1 / Recall@3 / Recall@5 correctness (synthetic ranked results)
# ============================================================================


def test_recall_at_1_correct_for_hit_and_miss() -> None:
    hit = evaluate.evaluate_question(_q(expected=("10",)), retrieved_article_nos=["10", "20", "30", "40", "50"])
    miss = evaluate.evaluate_question(_q(expected=("99",)), retrieved_article_nos=["10", "20", "30", "40", "50"])

    summary = evaluate.summarize([hit, miss])
    assert summary.any_hit_count_at_1 == 1
    assert summary.any_recall_at_1 == pytest.approx(0.5)


def test_recall_at_3_correct() -> None:
    # Expected article first appears at rank 3 - not a Recall@1 hit, but IS a Recall@3 hit.
    qe = evaluate.evaluate_question(_q(expected=("30",)), retrieved_article_nos=["10", "20", "30", "40", "50"])
    assert qe.any_hit_at_1 is False
    assert qe.any_hit_at_3 is True

    summary = evaluate.summarize([qe])
    assert summary.any_recall_at_3 == pytest.approx(1.0)


def test_recall_at_5_correct() -> None:
    # Expected article only appears at rank 5 - a Recall@5 hit, but not Recall@1/@3.
    qe = evaluate.evaluate_question(_q(expected=("50",)), retrieved_article_nos=["10", "20", "30", "40", "50"])
    assert qe.any_hit_at_1 is False
    assert qe.any_hit_at_3 is False
    assert qe.any_hit_at_5 is True

    summary = evaluate.summarize([qe])
    assert summary.any_recall_at_1 == pytest.approx(0.0)
    assert summary.any_recall_at_5 == pytest.approx(1.0)


# ============================================================================
# 4-5: ANY-match vs ALL-match for multi-article ground truth
# ============================================================================


def test_any_match_true_all_match_false_when_only_one_of_two_expected_present() -> None:
    qe = evaluate.evaluate_question(
        _q(expected=("10", "11")), retrieved_article_nos=["20", "11", "30", "40", "50"]
    )
    assert qe.any_hit_at_3 is True
    assert qe.all_hit_at_3 is False


def test_all_match_becomes_true_when_all_expected_articles_appear() -> None:
    qe = evaluate.evaluate_question(
        _q(expected=("10", "11")), retrieved_article_nos=["10", "20", "11", "40", "50"]
    )
    assert qe.any_hit_at_3 is True
    assert qe.all_hit_at_3 is True
    assert qe.all_hit_at_1 is False  # "11" not yet present within Top-1


# ============================================================================
# 6-7: article number normalization
# ============================================================================


def test_normalization_slash_matches_dash_variant() -> None:
    qe = evaluate.evaluate_question(_q(expected=("42/A",)), retrieved_article_nos=["42-a", "1", "2", "3", "4"])
    assert qe.any_hit_at_1 is True


def test_normalization_underscore_matches_slash_variant() -> None:
    qe = evaluate.evaluate_question(_q(expected=("42_A",)), retrieved_article_nos=["42/A", "1", "2", "3", "4"])
    assert qe.any_hit_at_1 is True


def test_normalize_article_no_does_not_merge_unrelated_articles() -> None:
    assert evaluate.normalize_article_no("42") != evaluate.normalize_article_no("43")
    assert evaluate.normalize_article_no("42/a") != evaluate.normalize_article_no("42/b")


def test_normalize_article_no_handles_surrounding_whitespace() -> None:
    assert evaluate.normalize_article_no("  42 / A  ") == "42/a"


# ============================================================================
# 8-11: first_expected_rank
# ============================================================================


def test_first_expected_rank_is_1() -> None:
    qe = evaluate.evaluate_question(_q(expected=("10",)), retrieved_article_nos=["10", "20", "30", "40", "50"])
    assert qe.first_expected_rank == 1


def test_first_expected_rank_is_3() -> None:
    qe = evaluate.evaluate_question(_q(expected=("30",)), retrieved_article_nos=["10", "20", "30", "40", "50"])
    assert qe.first_expected_rank == 3


def test_first_expected_rank_is_5() -> None:
    qe = evaluate.evaluate_question(_q(expected=("50",)), retrieved_article_nos=["10", "20", "30", "40", "50"])
    assert qe.first_expected_rank == 5


def test_first_expected_rank_none_when_absent_from_top5() -> None:
    qe = evaluate.evaluate_question(_q(expected=("99",)), retrieved_article_nos=["10", "20", "30", "40", "50"])
    assert qe.first_expected_rank is None
    assert qe.any_hit_at_5 is False


# ============================================================================
# 12: duplicate chunks from the same article never distort set matching
# ============================================================================


def test_duplicate_chunks_from_same_article_do_not_create_false_all_match() -> None:
    # Article "10" appears 5 times (e.g. a multi-chunk article); article "20"
    # never appears at all. all_hit_at_5 must stay False - 5 physical chunk
    # rows must never be mistaken for 5 distinct matched articles.
    qe = evaluate.evaluate_question(
        _q(expected=("10", "20")), retrieved_article_nos=["10", "10", "10", "10", "10"]
    )
    assert qe.any_hit_at_5 is True
    assert qe.all_hit_at_5 is False


def test_duplicate_chunks_still_yield_correct_first_rank() -> None:
    qe = evaluate.evaluate_question(
        _q(expected=("10",)), retrieved_article_nos=["20", "10", "10", "10", "10"]
    )
    assert qe.first_expected_rank == 2  # true first occurrence, not collapsed


# ============================================================================
# 13-14: malformed ground truth raises EvaluationError
# ============================================================================


def test_empty_expected_articles_raises(tmp_path: Path) -> None:
    path = _write_questions(tmp_path, [{"id": "q1", "question": "Soru?", "expected_articles": []}])
    with pytest.raises(evaluate.EvaluationError):
        evaluate.load_questions(path)


def test_missing_expected_articles_raises(tmp_path: Path) -> None:
    path = _write_questions(tmp_path, [{"id": "q1", "question": "Soru?"}])
    with pytest.raises(evaluate.EvaluationError):
        evaluate.load_questions(path)


def test_empty_question_text_raises(tmp_path: Path) -> None:
    path = _write_questions(tmp_path, [{"id": "q1", "question": "   ", "expected_articles": ["10"]}])
    with pytest.raises(evaluate.EvaluationError):
        evaluate.load_questions(path)


def test_empty_id_raises(tmp_path: Path) -> None:
    path = _write_questions(tmp_path, [{"id": "", "question": "Soru?", "expected_articles": ["10"]}])
    with pytest.raises(evaluate.EvaluationError):
        evaluate.load_questions(path)


def test_non_string_expected_article_entry_raises(tmp_path: Path) -> None:
    path = _write_questions(tmp_path, [{"id": "q1", "question": "Soru?", "expected_articles": [10]}])
    with pytest.raises(evaluate.EvaluationError):
        evaluate.load_questions(path)


# ============================================================================
# 15: empty evaluation dataset handled explicitly and safely
# ============================================================================


def test_empty_question_set_file_raises(tmp_path: Path) -> None:
    path = _write_questions(tmp_path, [])
    with pytest.raises(evaluate.EvaluationError):
        evaluate.load_questions(path)


def test_summarize_empty_list_raises_instead_of_dividing_by_zero() -> None:
    with pytest.raises(evaluate.EvaluationError):
        evaluate.summarize([])


# ============================================================================
# 16: exclusive rank-distribution bins sum to total_questions
# ============================================================================


def test_rank_distribution_exclusive_bins_sum_to_total() -> None:
    questions = [
        evaluate.evaluate_question(_q(qid="r1", expected=("1",)), retrieved_article_nos=["1", "2", "3", "4", "5"]),
        evaluate.evaluate_question(_q(qid="r2", expected=("2",)), retrieved_article_nos=["1", "2", "3", "4", "5"]),
        evaluate.evaluate_question(_q(qid="r3", expected=("4",)), retrieved_article_nos=["1", "2", "3", "4", "5"]),
        evaluate.evaluate_question(_q(qid="r4", expected=("5",)), retrieved_article_nos=["1", "2", "3", "4", "5"]),
        evaluate.evaluate_question(_q(qid="r5", expected=("99",)), retrieved_article_nos=["1", "2", "3", "4", "5"]),
    ]
    summary = evaluate.summarize(questions)
    assert (
        summary.rank_1_count + summary.rank_2_3_count + summary.rank_4_5_count + summary.not_in_top5_count
        == summary.total_questions
        == 5
    )
    assert summary.rank_1_count == 1
    assert summary.rank_2_3_count == 1
    assert summary.rank_4_5_count == 2
    assert summary.not_in_top5_count == 1


# ============================================================================
# 17: ANY/ALL metrics coincide for single-article questions
# ============================================================================


@pytest.mark.parametrize(
    "retrieved",
    [
        ["10", "20", "30", "40", "50"],
        ["20", "10", "30", "40", "50"],
        ["20", "30", "40", "50", "10"],
        ["20", "30", "40", "50", "60"],
    ],
)
def test_any_and_all_match_coincide_for_single_article_questions(retrieved: list[str]) -> None:
    qe = evaluate.evaluate_question(_q(expected=("10",)), retrieved_article_nos=retrieved)
    assert qe.any_hit_at_1 == qe.all_hit_at_1
    assert qe.any_hit_at_3 == qe.all_hit_at_3
    assert qe.any_hit_at_5 == qe.all_hit_at_5


# ============================================================================
# 18: tests/questions.json loader never modifies the source file
# ============================================================================


def test_questions_json_loader_preserves_source_data() -> None:
    path = evaluate.DEFAULT_QUESTIONS_PATH
    before = path.read_bytes()

    questions = evaluate.load_questions(path)

    after = path.read_bytes()
    assert after == before  # byte-identical: the loader never writes to disk

    by_id = {q.id: q for q in questions}
    assert by_id["q001"].expected_articles == ("2",)
    assert by_id["q001"].question == "Kabahat nedir?"
    assert len(questions) == 15


# ============================================================================
# Extra: EvaluationQuestion normalization / dedup
# ============================================================================


def test_duplicate_normalized_expected_articles_are_deduplicated() -> None:
    path_data = [{"id": "q1", "question": "Soru?", "expected_articles": ["10", "10"]}]
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "q.json"
        path.write_text(json.dumps(path_data), encoding="utf-8")
        questions = evaluate.load_questions(path)
    assert questions[0].normalized_expected_articles == frozenset({"10"})


# ============================================================================
# Extra: evaluate_all wiring (retrieve() called exactly once per question)
# ============================================================================


class _FakeEmbeddingItem:
    def __init__(self, index: int, embedding: list[float]) -> None:
        self.index = index
        self.embedding = embedding


class _FakeUsage:
    def __init__(self, prompt_tokens: int, total_tokens: int) -> None:
        self.prompt_tokens = prompt_tokens
        self.total_tokens = total_tokens


class _FakeResponse:
    def __init__(self, data: list[_FakeEmbeddingItem]) -> None:
        self.data = data
        self.usage = _FakeUsage(prompt_tokens=3, total_tokens=3)


class _FakeEmbeddingsResource:
    def __init__(self, vector: list[float]) -> None:
        self._vector = vector
        self.calls: list[tuple[str, list[str]]] = []

    def create(self, *, model: str, input: list[str]) -> _FakeResponse:  # noqa: A002
        self.calls.append((model, list(input)))
        return _FakeResponse(data=[_FakeEmbeddingItem(index=i, embedding=self._vector) for i in range(len(input))])


class _FakeClient:
    def __init__(self, vector: list[float]) -> None:
        self.embeddings = _FakeEmbeddingsResource(vector)


def _chunk(chunk_id: str, article_no: str) -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        article_id=f"5326-madde-{article_no}",
        document_id="5326_kabahatler_kanunu",
        legislation_number="5326",
        article_no=article_no,
        article_type="normal",
        article_title="Başlık",
        section_context=None,
        text=f"Madde {article_no} metni.",
        paragraph_numbers=None,
        source_paragraph_start=1,
        source_paragraph_end=1,
    )


def test_evaluate_all_calls_retrieve_exactly_once_per_question(tmp_path: Path) -> None:
    client = index.get_client(tmp_path)
    collection = index.get_collection(client, "test-evaluate")

    chunks = [_chunk("c-2", "2"), _chunk("c-13", "13")]
    results = [
        EmbeddingResult(chunk_id="c-2", embedding=[1.0, 0.0], model="fake-model"),
        EmbeddingResult(chunk_id="c-13", embedding=[0.0, 1.0], model="fake-model"),
    ]
    index.index_chunks(chunks, results, collection=collection)

    fake_client = _FakeClient([1.0, 0.0])
    questions = [_q(qid="q001", question="Kabahat nedir?", expected=("2",))]

    summary = evaluate.evaluate_all(questions, collection=collection, client=fake_client, top_k=5)

    assert len(fake_client.embeddings.calls) == 1  # exactly one embedding call for one question
    assert summary.total_questions == 1
    assert summary.any_hit_count_at_1 == 1
