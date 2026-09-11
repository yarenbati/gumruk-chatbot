"""Offline oracle-scope, exhaustive-coverage and rank-delta checks."""
from copy import deepcopy

import pytest

from scripts import run_m12fc_oracle_decomposition as oracle


def _question() -> dict:
    return dict(id="fixture",question="Original query",expected_document_ids=[oracle.DOCUMENT],
                expected_sources=[dict(document_id=oracle.DOCUMENT,article_type="normal",article_no="3")])


def _ranks() -> list[dict]:
    return [dict(rank=i,chunk_id=f"chunk-{i}",document_id=oracle.DOCUMENT,
                 document_source_key=f"{oracle.DOCUMENT}/normal/{i}",distance=i/100) for i in range(1,47)]


def test_enrichment_preserves_raw_bytes() -> None:
    raw = "  Özgün soru?\nİkinci satır  "
    title = "Admitted title"
    assert oracle.enriched_input(title,raw).encode() == title.encode()+b"\n\n"+raw.encode()


def test_oracle_requires_exact_exhaustive_chunk_set() -> None:
    ranks = _ranks()
    ids = {r["chunk_id"] for r in ranks}
    oracle.oracle_validate(_question(),ranks,ids)
    with pytest.raises(RuntimeError,match="ORACLE CORPUS SOURCE MISSING"):
        oracle.oracle_validate(_question(),ranks[:-1],ids)
    bad = deepcopy(ranks)
    bad[-1] = bad[0]
    with pytest.raises(RuntimeError,match="ORACLE CORPUS SOURCE MISSING"):
        oracle.oracle_validate(_question(),bad,ids)


def test_oracle_rejects_missing_gold_and_wrong_document() -> None:
    ranks = _ranks()
    ids = {r["chunk_id"] for r in ranks}
    ranks[2]["document_source_key"] = oracle.DOCUMENT+"/normal/99"
    with pytest.raises(RuntimeError,match="ORACLE CORPUS SOURCE MISSING"):
        oracle.oracle_validate(_question(),ranks,ids)
    ranks = _ranks()
    ranks[0]["document_id"] = "wrong_document"
    with pytest.raises(RuntimeError,match="ORACLE FILTER ERROR"):
        oracle.oracle_validate(_question(),ranks,ids)


@pytest.mark.parametrize("rank,band",[(1,"1"),(2,"2-3"),(3,"2-3"),(4,"4-5"),(5,"4-5"),(6,"6-10"),(10,"6-10"),(11,"11-20"),(20,"11-20"),(21,"21-30"),(30,"21-30"),(31,"31-46"),(46,"31-46")])
def test_rank_band_boundaries(rank: int, band: str) -> None:
    assert oracle.rank_band(rank) == band


def test_rank_delta_counts_do_not_hide_regression() -> None:
    result = oracle.delta_summary([-10,-2,0,0,7])
    assert result == dict(count=5,mean=-1,median=0,improved=2,unchanged=2,regressed=1)
    with pytest.raises(ValueError):
        oracle.rank_band(50)


def test_paired_coverage_keeps_unchanged_flags_separate() -> None:
    rows = []
    for i,(old,new) in enumerate(((False,True),(True,False),(True,True))):
        variants = {v:dict(metrics={str(k):{m:value for m in ("document_hit","document_all","source_any","source_all")} for k in oracle.CUTOFFS}) for v,value in (("G0",old),("O2",new))}
        rows.append(dict(question=dict(id=str(i)),variants=variants))
    paired = oracle._paired(rows,"G0","O2")
    assert paired["source_all"]["50"] == dict(improved=dict(count=1,ids=["0"]),unchanged=dict(count=1,ids=["2"]),regressed=dict(count=1,ids=["1"]))


def test_reviewed_population_and_oracle_gold_scope() -> None:
    questions = oracle.population()
    assert len(questions) == 30
    assert all(q.expected_document_ids == frozenset({oracle.DOCUMENT}) for q in questions)
