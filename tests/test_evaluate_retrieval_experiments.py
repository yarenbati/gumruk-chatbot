"""Offline deterministic M10E-A tests; no network or production Chroma."""

from __future__ import annotations

import inspect
import json
import math
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src import config, evaluate_retrieval_experiments as e


def _doc(cid: str, text: str = "eşya", law: str = "4458", article: str = "1", kind: str = "normal") -> e.Document:
    return e.Document(cid, text, {"legislation_number": law, "article_type": kind, "article_no": article})


def test_turkish_tokenization() -> None:
    assert e.tokenize("İTHALAT, IŞIK; ÇĞÖŞÜ ıi / 35_A --") == ["ithalat", "ışık", "çğöşü", "ıi", "35", "a"]
    assert e.tokenize("I\u0307THALAT") == ["ithalat"]
    assert e.tokenize("  , _ -- \n") == []
    assert e.tokenize("gümrük gümrükte") == ["gümrük", "gümrükte"]


def test_bm25_formula_and_ranking() -> None:
    index = e.BM25([_doc("a", "eşya eşya"), _doc("b", "eşya vergi"), _doc("c", "vergi vergi")])
    ranked = index.rank("eşya")
    assert [cid for cid, _ in ranked] == ["a", "b"]
    idf = math.log(1 + (3 - 2 + 0.5) / (2 + 0.5))
    assert ranked[0][1] == pytest.approx(idf * 2 * 2.5 / (2 + 1.5))
    assert ranked[1][1] == pytest.approx(idf)
    assert index.rank("eşya eşya") == ranked
    assert index.rank("bilinmeyen") == []


def test_bm25_ties_and_empty_documents() -> None:
    assert e.BM25([_doc("b"), _doc("a")]).rank("eşya")[0][0] == "a"
    assert e.BM25([_doc("a", "")]).rank("eşya") == []
    with pytest.raises(ValueError):
        e.BM25([_doc("a"), _doc("a")])


def test_rrf_formula_and_missing_membership() -> None:
    scores = dict(e.rrf(["a", "b"], ["c", "a"]))
    assert scores["a"] == pytest.approx(1 / 61 + 1 / 62)
    assert scores["b"] == pytest.approx(1 / 62)
    assert scores["c"] == pytest.approx(1 / 61)
    assert e.rrf([], []) == []


def test_rrf_deterministic_tie_breaking() -> None:
    assert [cid for cid, _ in e.rrf(["b", "a"], ["a", "b"])] == ["a", "b"]
    assert e.rrf(["b", "a"], ["a", "b"]) == e.rrf(["a", "b"], ["b", "a"])
    with pytest.raises(ValueError):
        e.rrf(["a", "a"], [])


def test_deduplicate_preserves_law_type_and_normalized_identity() -> None:
    docs = [_doc("first", article="42/A"), _doc("duplicate", article="42-a"),
            _doc("other-law", law="5326", article="42/A"),
            _doc("temporary", kind="gecici"), _doc("unincorporated", kind="islenemeyen_hukum"),
            _doc("normal"), _doc("other-article", article="2")]
    assert e.deduplicate([d.id for d in docs], {d.id: d for d in docs}) == [
        "first", "other-law", "temporary", "unincorporated", "normal", "other-article"]


def test_no_gold_fields_in_lexical_text_or_strategy_interface() -> None:
    doc = _doc("a", "eşya")
    poisoned = replace(doc, metadata={**doc.metadata, "expected_sources": "gizli",
                                     "expected_legislation": "gizli", "question_id": "gizli"})
    assert doc.lexical_text == poisoned.lexical_text == "eşya"
    assert e.BM25([poisoned]).rank("gizli") == []
    assert list(inspect.signature(e.local_variants).parameters) == ["query", "dense_ids", "lexical"]
    assert list(inspect.signature(e.collect_dense).parameters) == ["query", "collection", "client"]
    before = e.local_variants("eşya", ["a"], e.BM25([doc]))["rankings"]
    after = e.local_variants("eşya", ["a"], e.BM25([poisoned]))["rankings"]
    assert before == after


def test_one_dense_payload_reused_across_variants(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = SimpleNamespace(results=[SimpleNamespace(chunk_id="a")])
    fake = Mock(return_value=payload)
    monkeypatch.setattr(e.retrieve, "retrieve", fake)
    query = "  Özgün SORU?  "
    collection, client = object(), object()
    returned = e.collect_dense(query, collection=collection, client=client)
    result = e.local_variants(query, [r.chunk_id for r in returned.results], e.BM25([_doc("a", "soru")]))
    fake.assert_called_once_with(query, collection=collection, client=client,
                                 model=config.EMBEDDING_MODEL, top_k=20)
    assert returned is payload
    assert set(result["rankings"]) == {"B1", "B2", "B3"}
    assert all(ranking == ["a"] for ranking in result["rankings"].values())


def test_deduplication_uses_candidates_beyond_top5() -> None:
    docs = [_doc(str(i), article="1" if i < 6 else str(i)) for i in range(1, 10)]
    ids = [d.id for d in docs]
    result = e.local_variants("unknown", ids, e.BM25(docs))
    assert result["rankings"]["B2"][:5] == ["1", "2", "3", "4", "5"]
    assert result["rankings"]["B3"][:5] == ["1", "6", "7", "8", "9"]


def test_metrics_partial_multisource_and_intrusion() -> None:
    q = dict(id="example", question="test", dataset="4458", expected_sources=["4458/normal/1", "4458/normal/2"],
             expected_legislations=["4458"], case_type="multi_part", difficulty="hard")
    ranks = [{"rank": 1, "chunk_id": "a", "qualified_source_key": "5326/normal/1", "legislation_number": "5326"},
             {"rank": 2, "chunk_id": "b", "qualified_source_key": "4458/normal/1", "legislation_number": "4458"}]
    row = e.score(q, ranks)
    assert row["any_source_hit_at_1"] is False
    assert row["any_source_hit_at_3"] is True
    assert row["all_sources_match_at_5"] is False
    assert row["expected_source_ranks"] == {"4458/normal/1": 2, "4458/normal/2": None}
    assert row["non_expected_legislation_share_at_5"] == 0.5
    empty = e.score(q, [])
    summary = e.summarize([row, empty])
    assert summary["any_qualified_recall_at_5"] == 0.5
    assert summary["legislation_hit_at_5"] == 0.5
    assert summary["top1_unexpected_legislation_rate"] == 1.0
    assert summary["average_non_expected_legislation_share_at_5"] == 0.5


def test_all_frozen_metric_parity() -> None:
    baseline = json.loads(e.BASELINE.read_text(encoding="utf-8"))
    rows = []
    for question in baseline["results"]:
        result = e.score(question, question["ranks"])
        for key in result.keys() & question.keys():
            assert result[key] == question[key], (question["id"], key)
        rows.append(result)
    summaries = e.breakdown(rows)
    for subset in ("5326", "4458", "combined"):
        for key, value in baseline["summary_" + subset].items():
            if key != "error_count":
                assert summaries[subset][key] == value


def test_prefix_ids_and_keys_are_separate() -> None:
    old = [{"chunk_id": "a", "qualified_source_key": "4458/normal/1"}]
    new = [{"chunk_id": "b", "qualified_source_key": "4458/normal/1"}]
    comparison = e.prefix_comparison(old, new)
    assert comparison["exact_chunk_id_ranking_match"] is False
    assert comparison["qualified_key_sequence_match"] is True


def test_run_gate_and_existing_output(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("RUN_OPENAI_INTEGRATION_TESTS", "0")
    with pytest.raises(RuntimeError, match="Requires"):
        e.main()
    output = tmp_path / "already.json"
    output.write_text("{}")
    monkeypatch.setattr(e, "OUTPUT", output)
    monkeypatch.setattr(config, "OPENAI_API_KEY", "offline-test-placeholder")
    monkeypatch.setenv("RUN_OPENAI_INTEGRATION_TESTS", "1")
    with pytest.raises(RuntimeError, match="second real run"):
        e.main()


def test_identical_baseline_is_not_an_improving_candidate() -> None:
    baseline = json.loads(e.BASELINE.read_text(encoding="utf-8"))
    summary = e.breakdown([e.score(q, q["ranks"]) for q in baseline["results"]])
    result = e.recommend({strategy: summary for strategy in ("B0", "B1", "B2", "B3")})
    assert result["recommended_candidate"] is None
    assert all(a["criteria"]["5326_preserved"] for a in result["assessments"].values())
