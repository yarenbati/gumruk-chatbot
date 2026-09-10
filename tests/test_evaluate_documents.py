"""Offline document evaluation contracts and historical identity parity."""
from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from src import evaluate_documents as d, source_identity as identity
from src import evaluate_multilaw as legacy, retrieve


def key(document="document_a", article="1", kind="normal"):
    return identity.DocumentSourceKey(document, kind, article)


def question(*sources, id="test"):
    sources = sources or (key(),)
    return d.DocumentQuestion(id, "Synthetic question?", sources, {k.document_id for k in sources})


def chunks(*sources):
    return [retrieve.RetrievedChunk(i, f"chunk-{i}", "Synthetic text", k.to_dict(), i / 10)
            for i, k in enumerate(sources, 1)]


def test_question_immutable_canonical_and_duplicate_handling():
    sources = [key(article="42/A"), key(article="42-a")]
    q = d.DocumentQuestion("id", "Question?", sources, ["document_a", "document_a"])
    sources.clear()
    assert q.expected_sources == frozenset({key(article="42/a")})
    assert q.expected_document_ids == frozenset({"document_a"})
    with pytest.raises(FrozenInstanceError):
        q.id = "other"


@pytest.mark.parametrize("changes", [
    {"id": ""}, {"id": None}, {"question": "  "}, {"expected_sources": []},
    {"expected_sources": ["4458/normal/27"]}, {"expected_sources": None},
    {"expected_document_ids": ["other"]}, {"expected_document_ids": "document_a"},
    {"expected_document_ids": [None]},
])
def test_invalid_question(changes):
    args = dict(id="test", question="Question?", expected_sources=[key()], expected_document_ids=["document_a"])
    args.update(changes)
    with pytest.raises(d.DocumentEvaluationError):
        d.DocumentQuestion(**args)


def test_rank_from_actual_retrieved_chunk_is_observational():
    chunk = chunks(key(article="165/A"))[0]
    before = deepcopy(chunk)
    rank = d.DocumentRank.from_retrieved(chunk)
    assert chunk == before
    assert rank.document_source_key == key(article="165/a")
    assert rank.legislation_number is None
    assert rank.chunk_id == chunk.chunk_id and rank.rank == chunk.rank
    with pytest.raises(FrozenInstanceError):
        rank.rank = 9


@pytest.mark.parametrize("field,value", [
    ("document_id", None), ("document_id", "BAD"), ("article_type", None),
    ("article_type", "annex"), ("article_no", None), ("article_no", "42//"),
])
def test_bad_canonical_metadata_fails_even_below_cutoffs(field, value):
    ranked = chunks(*([key()] * 6))
    ranked[5].metadata[field] = value
    ranked[5].metadata["legislation_number"] = "5326"
    with pytest.raises(d.DocumentEvaluationError):
        d.evaluate_retrieved(question(), ranked)


@pytest.mark.parametrize("field", ["document_id", "article_type", "article_no"])
def test_missing_field_never_falls_back(field):
    chunk = chunks(key())[0]
    del chunk.metadata[field]
    chunk.metadata["legislation_number"] = "5326"
    with pytest.raises(d.DocumentEvaluationError):
        d.DocumentRank.from_retrieved(chunk)


@pytest.mark.parametrize("changes", [{"rank": 0}, {"rank": True}, {"chunk_id": ""},
    {"document_id": "different"}, {"document_source_key": "document_a/normal/1"}, {"legislation_number": 0}])
def test_invalid_direct_rank(changes):
    args = dict(rank=1, chunk_id="c", document_source_key=key(), document_id="document_a")
    args.update(changes)
    with pytest.raises(d.DocumentEvaluationError):
        d.DocumentRank(**args)


@pytest.mark.parametrize("position,flags", [(1, (True,True,True)), (3,(False,True,True)), (5,(False,False,True)), (6,(False,False,False))])
def test_all_cutoffs_source_and_document_metrics(position, flags):
    sources = [key("document_b")] * 6
    sources[position-1] = key()
    result = d.evaluate_retrieved(question(), chunks(*sources))
    for field in ("source_any", "source_all", "document_hit", "document_all"):
        assert tuple(getattr(m, field) for m in result.metrics) == flags


def test_duplicate_slots_and_same_document_completeness():
    q = question(key(article="1"), key(article="2"))
    ranked = chunks(key(), key(), key(article="2"))
    result = d.evaluate_retrieved(q, ranked)
    first, third, fifth = result.metrics
    assert first.source_any and not first.source_all
    assert first.document_hit and first.document_all
    assert third.source_all and fifth.source_all
    assert len(result.ranks) == 3
    delayed = d.evaluate_retrieved(q, chunks(key(), key(), key(), key(article="2")))
    assert not delayed.metrics[1].source_all
    assert delayed.metrics[2].source_all


def test_true_multi_document():
    q = question(key(), key("document_b", "2"))
    result = d.evaluate_retrieved(q, chunks(key(), key("document_b", "2")))
    first, third, _ = result.metrics
    assert first.source_any and first.document_hit
    assert not first.source_all and not first.document_all
    assert third.source_all and third.document_all


def test_intrusion_counts_slots_not_unique_documents():
    result = d.evaluate_retrieved(question(), chunks(key(), key("document_b"), key(), key("document_b"), key()))
    assert [m.document_intrusion for m in result.metrics] == [0, 1/3, .4]
    short = d.evaluate_retrieved(question(), chunks(key("document_b")))
    assert [m.document_intrusion for m in short.metrics] == [1,1,1]
    assert [m.retrieved_slots for m in short.metrics] == [1,1,1]


def test_empty_ranking_has_undefined_intrusion():
    result = d.evaluate_retrieved(question(), [])
    for metric in result.metrics:
        assert not any((metric.source_any, metric.source_all, metric.document_hit, metric.document_all))
        assert metric.document_intrusion is None and metric.retrieved_slots == 0


def test_numberless_regulation_participates_in_every_metric():
    q = question(key("synthetic_regulation"))
    result = d.evaluate_retrieved(q, chunks(key("synthetic_regulation"), key("document_b")))
    assert all((m.source_any and m.source_all and m.document_hit and m.document_all) for m in result.metrics)
    assert [m.document_intrusion for m in result.metrics] == [0,.5,.5]
    assert all(r.legislation_number is None for r in result.ranks)
    assert "say" not in json.dumps(result.to_dict())


def test_rank_order_is_never_silently_repaired():
    ranks = [d.DocumentRank.from_retrieved(c) for c in chunks(key(), key("document_b"))]
    with pytest.raises(d.DocumentEvaluationError, match="sequential"):
        d.evaluate_question(question(), ranks[::-1])


def test_schema_roundtrip_order_and_fresh_serialization():
    a, b = question(key(article="165/A"), id="a"), question(key("document_b"), id="b")
    payload = d.dataset_to_dict([b,a])
    assert d.dataset_from_dict(json.loads(json.dumps(payload))) == (a,b)
    assert payload == d.dataset_to_dict([a,b])
    assert payload["source_identity_schema"] == "document-source-v1"
    result = d.evaluate_retrieved(a, chunks(key(article="165/a")))
    assert result.to_dict()["ranks"][0]["document_source_key"] == "document_a/normal/165/a"
    assert json.loads(json.dumps(result.to_dict())) == result.to_dict()
    payload["questions"][0]["expected_sources"].clear()
    assert a.expected_sources


@pytest.mark.parametrize("schema", [None, "qualified-source-v1", "4458/normal/27"])
def test_undeclared_or_legacy_schema_rejected(schema):
    payload = d.dataset_to_dict([question()])
    if schema is None:
        del payload["source_identity_schema"]
    else:
        payload["source_identity_schema"] = schema
    with pytest.raises(d.DocumentEvaluationError):
        d.dataset_from_dict(payload)


def test_legacy_strings_and_duplicate_question_ids_rejected():
    payload = d.dataset_to_dict([question()])
    payload["questions"][0]["expected_sources"] = ["4458/normal/27"]
    with pytest.raises(d.DocumentEvaluationError):
        d.dataset_from_dict(payload)
    with pytest.raises(d.DocumentEvaluationError):
        d.dataset_to_dict([question(),question()])


@pytest.mark.parametrize("law,document", [("5326","5326_kabahatler_kanunu"), ("4458","4458_gumruk_kanunu")])
def test_legacy_adapter_and_actual_historical_metric_parity(law, document):
    expected = frozenset([legacy.QualifiedSourceKey.build(law, "normal", "165/A"),
                          legacy.QualifiedSourceKey.build(law, "gecici", "1")])
    old = legacy.MultiLawQuestion("old", "Unchanged?", law, expected, frozenset([law]))
    original = deepcopy(old)
    new = d.adapt_legacy_question(old)
    assert new.expected_document_ids == frozenset([document])
    distractor = legacy.QualifiedSourceKey.build("4458" if law == "5326" else "5326", "normal", "165/A")
    observed_all = set()
    for gold_position in range(1,7):
        keys = [distractor] * 6
        keys[gold_position-1] = legacy.QualifiedSourceKey.build(law,"normal","165/a")
        second_position = 0 if gold_position % 2 == 0 else 5
        keys[second_position] = legacy.QualifiedSourceKey.build(law,"gecici","1")
        old_chunks = [retrieve.RetrievedChunk(i, f"c{i}", "fixture", dict(
            legislation_number=k.legislation_number, article_type=k.article_type, article_no=k.article_no), 0)
            for i,k in enumerate(keys,1)]
        old_ranks = legacy._extract_rank_info(old_chunks)
        new_chunks = [replace(c, metadata=dict(c.metadata, document_id=identity.CURRENT_LEGACY_REGISTRY[k.legislation_number]))
                      for c,k in zip(old_chunks,keys)]
        result = d.evaluate_retrieved(new, new_chunks)
        for m in result.metrics:
            assert m.source_any == legacy._any_hit(expected,old_ranks,m.k)
            assert m.source_all == legacy._all_match(expected,old_ranks,m.k)
            observed_all.add(m.source_all)
        assert all("document_id" not in c.metadata for c in old_chunks)
    assert observed_all == {False, True}
    assert old == original


def test_unknown_legacy_mapping_fails():
    old = SimpleNamespace(id="old", question="Question?", expected_sources=[legacy.QualifiedSourceKey.build("5607","normal","1")])
    with pytest.raises(d.DocumentEvaluationError, match="unresolved"):
        d.adapt_legacy_question(old)


def test_summary_groups_rates_and_empty_denominators():
    a = d.evaluate_retrieved(question(id="a"), chunks(key()))
    b = d.evaluate_retrieved(question(key(),key(article="2"),id="b"), chunks(key()))
    c = d.evaluate_retrieved(question(key(),key("document_b"),id="c"), [])
    summary = d.summarize([c,b,a])
    assert summary == d.summarize([a,b,c])
    assert summary["overall"]["metrics"]["1"]["source_any"] == 2/3
    assert summary["overall"]["metrics"]["1"]["source_all"] == 1/3
    assert summary["overall"]["metrics"]["1"]["document_all"] == 2/3
    assert summary["overall"]["metrics"]["1"]["intrusion_defined_questions"] == 2
    assert summary["overall"]["metrics"]["1"]["intrusion_undefined_questions"] == 1
    assert summary["single_source"]["count"] == 1
    assert summary["multi_source"]["count"] == 2
    assert summary["single_document"]["count"] == 2
    assert summary["multi_document"]["count"] == 1
    assert summary["per_document"]["document_a"]["count"] == 3
    assert summary["per_document"]["document_b"]["count"] == 1
    assert d.summarize([])["overall"]["metrics"]["5"]["source_any"] is None
    assert json.loads(json.dumps(summary)) == summary
    with pytest.raises(d.DocumentEvaluationError):
        d.summarize([a,a])


def test_module_has_no_io_or_retrieval_dependencies():
    tree = ast.parse(Path(d.__file__).read_text(encoding="utf-8"))
    imports = [n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
    assert all(not any(x in (name or "") for x in ("openai","chromadb","retrieve","evaluate_multilaw")) for name in imports)
    calls = {n.func.attr for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)}
    assert not calls & {"retrieve","query","PersistentClient","read_text","write_text","load_manifest"}
