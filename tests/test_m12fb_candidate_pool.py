"""Offline tests for saved-prefix completeness and drift accounting."""
from copy import deepcopy

import pytest

from scripts import run_m12fb_candidate_pool as diagnostic
from src import evaluate_documents as ev


def _question() -> dict:
    return dict(id="example",question="Raw original query",expected_document_ids=["test_law"],
                expected_sources=[dict(document_id="test_law",article_type="normal",article_no=n) for n in ("2","3")])


def _ranks() -> list[dict]:
    rows = []
    for rank in range(1,51):
        number = "2" if rank in (7,8) else "3" if rank == 21 else "99"
        document = "test_law" if rank >= 3 else "other_law"
        rows.append(dict(rank=rank,chunk_id=f"chunk-{rank}",document_id=document,
                         document_source_key=f"{document}/normal/{number}",legislation_number=None,distance=rank/100))
    return rows


def test_multi_source_completeness_and_duplicate_slots() -> None:
    q,ranks = _question(),_ranks()
    found = diagnostic.first_ranks(q,ranks)
    assert found["first_expected_document_rank"] == 3
    assert found["first_expected_source_rank"] == 7
    assert found["all_expected_sources_recovered_by_rank"] == 21
    assert diagnostic.score_prefix(q,ranks,10)["source_any"]
    assert not diagnostic.score_prefix(q,ranks,20)["source_all"]
    assert diagnostic.score_prefix(q,ranks,50)["source_all"]
    assert diagnostic.duplicate_slots(ranks,8)["repeated_slots"] == 5
    assert len(ranks) == 50  # counting does not deduplicate the supplied ranking


def test_null_is_not_false_recovery() -> None:
    q,ranks = _question(),_ranks()[:20]
    found = diagnostic.first_ranks(q,ranks)
    assert found["all_expected_sources_recovered_by_rank"] is None
    assert found["expected_source_ranks"]["test_law/normal/3"] is None
    q["expected_sources"] = [q["expected_sources"][1]]
    assert diagnostic.first_ranks(q,ranks)["first_expected_source_rank"] is None


@pytest.mark.parametrize("rank, band",[(None,">50"),(1,"1-5"),(5,"1-5"),(6,"6-10"),(10,"6-10"),(11,"11-20"),(20,"11-20"),(21,"21-50"),(50,"21-50")])
def test_recovery_band_boundaries(rank: int | None, band: str) -> None:
    assert diagnostic.recovery_band(rank) == band


def test_existing_evaluator_agrees_on_supported_cutoffs() -> None:
    q,ranks = _question(),_ranks()
    question = ev.dataset_from_dict(dict(source_identity_schema="document-source-v1",questions=[q]))[0]
    parsed = [ev.DocumentRank(r["rank"],r["chunk_id"],ev.source_identity.DocumentSourceKey.parse(r["document_source_key"]),r["document_id"]) for r in ranks]
    expected = ev.evaluate_question(question,parsed).to_dict()["metrics"]
    assert all(diagnostic.score_prefix(q,ranks,int(k)) == value for k,value in expected.items())


def test_drift_is_separate_from_metric_recovery() -> None:
    q,ranks = _question(),_ranks()
    row = dict(question=q,ranks=ranks,metrics={str(k):diagnostic.score_prefix(q,ranks,k) for k in diagnostic.CUTOFFS})
    old = dict(ranks=deepcopy(ranks[:5]),metrics={k:row["metrics"][k] for k in ("1","3","5")})
    old["ranks"][0]["distance"] += 2e-7
    drift = diagnostic.drift_check(row,old)
    assert drift["top5_chunk_ids_equal"] and drift["metrics_equal"]
    assert not drift["slot_distances_equal"] and not drift["common_chunk_distances_equal"]
    old["ranks"][0]["distance"] = ranks[0]["distance"] + 1e-9
    assert diagnostic.drift_check(row,old)["slot_distances_equal"]


def test_exact_m12d_loader_population() -> None:
    questions = diagnostic._population()
    assert len(questions) == len({q.question for q in questions}) == 105
