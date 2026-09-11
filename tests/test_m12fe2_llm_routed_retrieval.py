"""Offline tests for the M12F-E2 saved-routing diagnostic."""
from __future__ import annotations

from scripts import run_m12fe2_llm_routed_retrieval as e2


def test_score_prefix_supports_multi_source_any_all() -> None:
    question = {"expected_sources": [{"document_id": "d", "article_type": "normal", "article_no": "3"}, {"document_id": "d", "article_type": "normal", "article_no": "4"}], "expected_document_ids": ["d"]}
    ranks = [{"document_source_key": "d/normal/3", "document_id": "d"}, {"document_source_key": "d/normal/9", "document_id": "d"}]
    score = e2.score_prefix(question, ranks, 2)
    assert score["source_any"] is True and score["source_all"] is False


def test_saved_router_prediction_validation_rejects_missing_document() -> None:
    question = e2._population()[0]
    router = {"status": "completed", "verdict": "M12F-E READY FOR REVIEW \u2014 LLM ROUTER PROMISING", "accuracy": {"all": {"top1": 100, "top2": 105}}, "routing_evaluation": {"by_true_document": {e2.m12d.DOCS["5607"]: {"top1": 27}}}, "results": [{"question": question.to_dict(), "prediction": [e2.m12d.DOCS["5326"], e2.m12d.DOCS["4458"], e2.m12d.DOCS["5607"]]} for question in e2._population()]}
    router["results"][0]["prediction"] = [e2.m12d.DOCS["5326"], e2.m12d.DOCS["4458"], e2.m12d.DOCS["5326"]]
    try:
        e2._validate_saved_router(router, e2._population())
    except AssertionError:
        pass
    else:
        raise AssertionError("duplicate saved document prediction was accepted")


def test_primary_cases_are_exactly_six() -> None:
    assert e2.PRIMARY == ["k5607-002", "k5607-003", "k5607-004", "k5607-025", "k5607-026", "k5607-029"]


def test_no_gold_fallback_is_explicit() -> None:
    assert e2.VARIANTS == ("B0", "R1", "R2")
