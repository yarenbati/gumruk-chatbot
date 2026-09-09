"""Offline M10D contract tests; retrieval is always replaced with ranked fixtures."""

from __future__ import annotations

import csv
import ast
import hashlib
import importlib
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src import config, evaluate, evaluate_multilaw as m, evaluation_dataset, retrieve


def _key(law: str = "4458", article: str = "27", kind: str = "normal") -> m.QualifiedSourceKey:
    return m.QualifiedSourceKey.build(law, kind, article)


def _question(*keys: m.QualifiedSourceKey) -> m.MultiLawQuestion:
    return m.MultiLawQuestion("example", "Unchanged query?", "4458", frozenset(keys), frozenset(k.legislation_number for k in keys))


def _chunks(*keys: m.QualifiedSourceKey) -> list[retrieve.RetrievedChunk]:
    return [retrieve.RetrievedChunk(i, f"chunk-{i}", "Do not infer identity from this text", {
        "legislation_number": k.legislation_number, "article_type": k.article_type, "article_no": k.article_no,
    }, float(i)) for i, k in enumerate(keys, 1)]


def _result(monkeypatch: pytest.MonkeyPatch, question: m.MultiLawQuestion, *keys: m.QualifiedSourceKey) -> m.QuestionResult:
    fake = Mock(return_value=SimpleNamespace(results=_chunks(*keys), embedding_usage=SimpleNamespace(total_tokens=3), latency_ms=2.0))
    monkeypatch.setattr(retrieve, "retrieve", fake)
    collection = object()
    result = m.evaluate_question(question, collection=collection)
    fake.assert_called_once_with(question.question, collection=collection, client=None, model=config.EMBEDDING_MODEL, top_k=config.TOP_K)
    return result


def test_qualified_identity() -> None:
    """Canonical identity retains law and type while normalizing article number."""
    assert _key(article=" 42 _ A ") == _key(article="42/a")
    assert _key("5326") != _key("4458")
    assert _key(article="1", kind="gecici") != _key(article="1", kind="islenemeyen_hukum")


@pytest.mark.parametrize("field", ["legislation_number", "article_type", "article_no"])
@pytest.mark.parametrize("value", [None, "", " ", 123])
def test_missing_metadata_fails(field: str, value: object) -> None:
    """Invalid identity is a contract error, never an ordinary retrieval miss."""
    chunks = _chunks(_key())
    chunks[0].metadata[field] = value
    with pytest.raises(m.MultiLawEvaluationError):
        m._extract_rank_info(chunks)


def test_any_all_and_legislation_independence(monkeypatch: pytest.MonkeyPatch) -> None:
    """One of two expected sources satisfies ANY but not ALL."""
    q = _question(_key(), _key(article="24"))
    r = _result(monkeypatch, q, _key(article="99"), _key("5326"), _key(), _key(), _key("5326"))
    assert (r.any_source_hit_at_1, r.any_source_hit_at_3, r.any_source_hit_at_5) == (False, True, True)
    assert (r.all_sources_match_at_1, r.all_sources_match_at_3, r.all_sources_match_at_5) == (False, False, False)
    assert (r.expected_legislation_hit_at_1, r.expected_legislation_hit_at_3, r.expected_legislation_hit_at_5) == (True, True, True)
    complete = _result(monkeypatch, q, _key(), _key(article="24"))
    assert complete.all_sources_match_at_3 and complete.all_sources_match_at_5
    single = _result(monkeypatch, _question(_key(), _key()), _key())
    assert single.any_source_hit_at_1 and single.all_sources_match_at_1


@pytest.mark.parametrize("position,expected", [(1, (True, True, True)), (3, (False, True, True)), (5, (False, False, True))])
def test_legislation_hit_depth(monkeypatch: pytest.MonkeyPatch, position: int, expected: tuple[bool, ...]) -> None:
    """Legislation hit uses the requested prefix independently of article identity."""
    keys = [_key("5326")] * 5
    keys[position - 1] = _key(article="99")
    r = _result(monkeypatch, _question(_key()), *keys)
    assert (r.expected_legislation_hit_at_1, r.expected_legislation_hit_at_3, r.expected_legislation_hit_at_5) == expected
    assert not r.any_source_hit_at_5


def test_top5_share_and_real_top1_confusion(monkeypatch: pytest.MonkeyPatch) -> None:
    """Rank six cannot alter Top-5 intrusion or the real Top-1 law."""
    r = _result(monkeypatch, _question(_key()), _key("5326"), _key(), _key(), _key("5326"), _key(), _key("5326"))
    assert r.non_expected_legislation_count_at_5 == 2
    assert r.non_expected_legislation_share_at_5 == 2 / 5
    assert r.top1_legislation == "5326"
    matrix = m.top1_legislation_confusion_matrix([r])
    assert matrix["matrix"] == {"5326": {"5326": 0, "4458": 0}, "4458": {"5326": 1, "4458": 0}}
    short = _result(monkeypatch, _question(_key()), _key("5326"), _key())
    assert short.non_expected_legislation_share_at_5 == 0.5
    empty = _result(monkeypatch, _question(_key()))
    assert empty.non_expected_legislation_share_at_5 is None
    assert m.top1_legislation_confusion_matrix([empty])["missing_top1_metadata"] == 1


def test_retrieval_failure_has_no_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    """A retrieval failure is reported after exactly one call."""
    fake = Mock(side_effect=retrieve.RetrievalError("private diagnostic"))
    monkeypatch.setattr(retrieve, "retrieve", fake)
    r = m.evaluate_question(_question(_key()), collection=object())
    assert fake.call_count == 1
    assert r.error_type == "RetrievalError"
    assert "private" not in r.safe_error


def test_frozen_5326_adapter() -> None:
    """The legacy dataset is wrapped without changing questions or article targets."""
    original = evaluation_dataset.load_m9b_benchmark()
    adapted = m.load_5326_questions()
    assert [q.id for q in adapted] == [f"q{i:03}" for i in range(1, 46)]
    for before, after in zip(original, adapted):
        assert before.question == after.question
        assert after.expected_sources == frozenset(_key("5326", a) for a in before.expected_articles)


def test_historical_pre_from_frozen_ranked_data() -> None:
    """PRE is derived from each frozen ranked row, ignoring aggregate scores."""
    frozen = m.load_frozen_m9b_provisional()
    lookup = m.build_5326_chunk_type_lookup(Path(__file__).parent / "fixtures" / "m10d_5326_chunk_metadata.json")
    frozen["summary"] = {"deliberately_unusable": True}
    outcomes = m.historical_5326_question_outcomes(frozen, lookup)
    assert len(outcomes) == 45
    for row in frozen["results"]:
        expected = {evaluate.normalize_article_no(a) for a in row["expected_articles"]}
        for k in (1, 3, 5):
            got = {evaluate.normalize_article_no(a) for a in row["retrieved_articles"][:k] if a is not None}
            assert outcomes[row["id"]][f"any_hit_at_{k}"] == bool(expected & got)
            assert outcomes[row["id"]][f"all_match_at_{k}"] == expected.issubset(got)
    assert outcomes["q001"] == {"any_hit_at_1": False, "any_hit_at_3": False, "any_hit_at_5": True,
                                 "all_match_at_1": False, "all_match_at_3": False, "all_match_at_5": True}
    with pytest.raises(m.MultiLawEvaluationError, match="metadata"):
        m.historical_5326_question_outcomes(frozen, {})


def test_historical_type_collision_is_not_a_match() -> None:
    """Historical metadata resolution never falls back to bare article numbers."""
    data = {"results": [{"id": "q", "expected_articles": ["1"], "retrieved_chunk_ids": ["temporary"], "retrieved_articles": ["1"]}]}
    result = m.historical_5326_question_outcomes(data, {"temporary": ("5326", "gecici", "1")})
    assert not any(result["q"].values())


def test_final_dataset_freeze() -> None:
    """Final data differs from the preserved candidate only at the approved wording."""
    final_bytes = m.QUESTIONS_4458_PATH.read_bytes()
    assert hashlib.sha256(final_bytes).hexdigest() == "bf81bb00f665435ace8ab28bbce274ba473074825501fcde0af34c98c45bb595"
    final = json.loads(final_bytes)
    candidate = json.loads(m.QUESTIONS_4458_CANDIDATE_PATH.read_text(encoding="utf-8"))
    assert len(m.load_4458_questions()) == len(final) == len(candidate) == 30
    assert [q["id"] for q in final] == [f"gk{i:03}" for i in range(1, 31)]
    assert all(q["expert_validated"] is False and q["source_verified"] is True for q in final)
    changes = []
    for before, after in zip(candidate, final):
        assert before["expected_sources"] == after["expected_sources"]
        changes.extend((before["id"], field) for field in before.keys() | after.keys() if before.get(field) != after.get(field))
    assert changes == [("gk007", "question"), ("gk019", "question"), ("gk022", "question")]
    review = m.PROJECT_ROOT / "reports/evaluation/m10d-4458-question-review.csv"
    with review.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert [r["id"] for r in rows] == [q["id"] for q in final]
    assert [r["question"] for r in rows] == [q["question"] for q in final]
    for row, question in zip(rows, final):
        assert row["expected_sources"] == " | ".join(
            f"{source['legislation_number']}/{source['article_type']}/{source['article_no']}"
            for source in question["expected_sources"]
        )
        assert row["case_type"] == question["case_type"]
        assert row["difficulty"] == question["difficulty"]
        assert row["source_verified"].lower() == "true"
        assert row["expert_validated"].lower() == "false"
        assert row["review_status"] == "pending"
        assert all(row[field] == "" for field in (
            "question_clear", "question_natural", "expected_sources_correct",
            "answerable_from_current_corpus", "ambiguous", "reviewer_notes",
        ))


def test_import_safe(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reloading the evaluator cannot open a collection or retrieve anything."""
    from src import index
    forbidden = Mock(side_effect=AssertionError("Import performed external work"))
    monkeypatch.setattr(index, "get_client", forbidden)
    monkeypatch.setattr(retrieve, "retrieve", forbidden)
    importlib.reload(m)
    forbidden.assert_not_called()


def test_regression_rejects_missing_ids() -> None:
    """A partial join must not silently change regression denominators."""
    with pytest.raises(m.MultiLawEvaluationError):
        m.compare_5326_regression([], {"q001": {}})


def test_retrieval_and_collection_call_contract() -> None:
    """Evaluator has one retrieval site, no mutation or generation call sites."""
    tree = ast.parse(Path(m.__file__).read_text(encoding="utf-8"))
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    forbidden = {"upsert", "delete", "reset", "create_collection", "delete_collection", "get_or_create_collection",
                 "run_rag", "generate_answer", "rebuild", "query", "embed_query", "embed_texts"}
    assert not [c for c in calls if isinstance(c.func, ast.Attribute) and c.func.attr in forbidden]
    production_calls = [c for c in calls if isinstance(c.func, ast.Attribute) and c.func.attr == "retrieve"]
    assert len(production_calls) == 1
    assert {kw.arg for kw in production_calls[0].keywords} == {"collection", "client", "model", "top_k"}
    assert m.EVAL_TOP_K == config.TOP_K


def test_collection_counts_are_read_only() -> None:
    """The inventory helper requests metadata only and reports actual law counts."""
    collection = SimpleNamespace(get=Mock(return_value={"metadatas": [c.metadata for c in _chunks(_key(), _key("5326"))]}))
    assert m._collection_law_counts(collection) == {"4458": 1, "5326": 1}
    collection.get.assert_called_once_with(include=["metadatas"])


def test_insufficient_depth_fails_before_retrieval(monkeypatch: pytest.MonkeyPatch) -> None:
    """Top-5 cannot be reported for an intentionally shallower query."""
    fake = Mock()
    monkeypatch.setattr(retrieve, "retrieve", fake)
    with pytest.raises(m.MultiLawEvaluationError):
        m.evaluate_question(_question(_key()), collection=object(), top_k=3)
    fake.assert_not_called()
