"""Offline invariants for M12F-E Phase A classification."""
from scripts import run_m12fe_llm_router as router


def test_validate_prediction_accepts_exact_supported_permutation() -> None:
    assert router.validate_prediction({"ranked_documents": list(router.DOCUMENT_IDS)}) == list(router.DOCUMENT_IDS)


def test_validate_prediction_rejects_duplicates_and_unknowns() -> None:
    for value in (
        {"ranked_documents": [router.DOCUMENT_IDS[0], router.DOCUMENT_IDS[0], router.DOCUMENT_IDS[1]]},
        {"ranked_documents": [router.DOCUMENT_IDS[0], router.DOCUMENT_IDS[1], "unknown"]},
    ):
        try:
            router.validate_prediction(value)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid prediction was accepted")


def test_accuracy_and_subgroups_use_prediction_only_until_scoring() -> None:
    rows = [
        {"question": {"id": "q1", "question": "Soru", "expected_document_ids": [router.DOCUMENT_IDS[0]], "expected_sources": [{"document_id": router.DOCUMENT_IDS[0], "article_type": "normal", "article_no": "1"}]}, "prediction": list(router.DOCUMENT_IDS), "classification": {}},
        {"question": {"id": "q2", "question": "Soru", "expected_document_ids": [router.DOCUMENT_IDS[1]], "expected_sources": [{"document_id": router.DOCUMENT_IDS[1], "article_type": "normal", "article_no": "1"}]}, "prediction": [router.DOCUMENT_IDS[0], router.DOCUMENT_IDS[1], router.DOCUMENT_IDS[2]], "classification": {}},
    ]
    result = router._accuracy(rows, "all")
    assert result["top1"] == 1 and result["top2"] == 2


def test_paired_centroid_accounting_and_primary_ids() -> None:
    rows = [{"question": {"id": "k5607-003", "question": "Soru", "expected_document_ids": [router.DOCUMENT_IDS[2]], "expected_sources": [{"document_id": router.DOCUMENT_IDS[2], "article_type": "normal", "article_no": "3"}]}, "prediction": [router.DOCUMENT_IDS[2], router.DOCUMENT_IDS[0], router.DOCUMENT_IDS[1]], "classification": {}}]
    centroid = {"k5607-003": {"routing": [{"document_id": router.DOCUMENT_IDS[0]}, {"document_id": router.DOCUMENT_IDS[2]}, {"document_id": router.DOCUMENT_IDS[1]}]}}
    assert router._paired(rows, centroid, 1)["llm_only"]["ids"] == ["k5607-003"]
    assert router._paired(rows, centroid, 2)["both_correct"]["ids"] == ["k5607-003"]
    assert router.PRIMARY[1] == "k5607-003"
