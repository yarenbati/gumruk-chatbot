"""Offline guardrails for the development-only explicit-law experiment."""
from types import SimpleNamespace

import pytest

from scripts import run_m12fa_explicit_law as exp


@pytest.mark.parametrize("text, expected", [
    ("5607 sayılı Kanun", ("5607",)),
    ("(4458), 5326; 5607", ("4458", "5326", "5607")),
    ("5607'nin 5607 sayılı", ("5607",)),
    ("15607 56070 a5607 5607b _5607 5607_ ş5607 5607ş", ()),
    ("Madde 3 fıkra 1; gümrük işlemleri", ()),
    ("4458\n5326", ("4458", "5326")),
])
def test_literal_detection(text: str, expected: tuple[str, ...]) -> None:
    assert exp.detect_laws(text) == expected


@pytest.mark.parametrize("law, document", [
    ("5326", "5326_kabahatler_kanunu"),
    ("4458", "4458_gumruk_kanunu"),
    ("5607", "5607_kacakcilikla_mucadele_kanunu"),
])
def test_exact_filter(law: str, document: str) -> None:
    assert exp.document_filter(law) == {"document_id":document}


def test_dataset_matches_reviewed_population() -> None:
    eligible, audit = exp.detector_audit()
    assert len(eligible) == 6 and audit["no_explicit_count"] == 99
    assert audit["breakdown"] == {"5326":0,"4458":0,"5607":6}
    assert audit["complete_miss_eligible"] == ["k5607-002"]
    assert audit["wrong_top1_eligible"] == ["k5607-002"]
    assert audit["ambiguous_count"] == audit["gold_contradictions"] == 0


def test_exact_pair_cache_and_response_index_order() -> None:
    calls = []

    class Endpoint:
        def create(self, **kwargs: object) -> SimpleNamespace:
            calls.append(kwargs)
            return SimpleNamespace(usage=SimpleNamespace(prompt_tokens=8,total_tokens=8),
                                   data=[SimpleNamespace(index=1,embedding=[2.0]*1536),
                                         SimpleNamespace(index=0,embedding=[1.0]*1536)])

    stats = dict(requests=0,successful_embeddings=0,failures=0,prompt_tokens=0,total_tokens=0)
    cache = exp.cached_embeddings(Endpoint(), [("model", "raw"), ("model", "title\n\nraw"), ("model", "raw")], stats)
    assert len(calls) == stats["requests"] == 1
    assert stats["unique_embedding_inputs"] == stats["successful_embeddings"] == 2
    assert calls[0]["input"] == ["raw", "title\n\nraw"]
    assert cache[("model", "raw")][0] == 1.0
    assert stats["total_tokens"] == 8


def test_embedding_failure_has_no_retry() -> None:
    class Endpoint:
        def create(self, **kwargs: object) -> None:
            raise RuntimeError("fake failure")

    stats = dict(requests=0,successful_embeddings=0,failures=0,prompt_tokens=0,total_tokens=0)
    with pytest.raises(RuntimeError):
        exp.cached_embeddings(Endpoint(), [("model","raw")], stats)
    assert stats["requests"] == stats["failures"] == 1


def test_paired_flags_preserve_gains_and_losses() -> None:
    rows = []
    for i, (before, after) in enumerate(((False,True),(True,False),(True,True))):
        variants = {v:dict(metrics={k:{m:value for m in exp.METRICS[:-1]} for k in ("1","3","5")})
                    for v,value in (("B0",before),("A1",after))}
        rows.append(dict(question=dict(id=str(i)),variants=variants))
    paired = exp.paired_counts(rows,"A1")
    for metric in exp.METRICS[:-1]:
        assert {name:value["count"] for name,value in paired[metric]["5"].items()} == {"improved":1,"unchanged":1,"regressed":1}
