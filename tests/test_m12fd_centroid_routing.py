"""Offline invariants for the M12F-D centroid router."""
from scripts import run_m12fd_centroid_routing as router


def test_normalize_returns_unit_vector() -> None:
    result = router._normalize([1.0] * router.DIMENSIONS)
    assert len(result) == router.DIMENSIONS
    assert abs(sum(x * x for x in result) - 1.0) < 1e-12


def test_route_is_similarity_descending_and_deterministic() -> None:
    vectors = {doc: [0.0] * router.DIMENSIONS for doc in router.DOC_IDS}
    vectors[router.DOC_IDS[0]][0] = 1.0
    vectors[router.DOC_IDS[1]][1] = 1.0
    vectors[router.DOC_IDS[2]][2] = 1.0
    assert router._route([1.0] + [0.0] * (router.DIMENSIONS - 1), vectors)[0]["document_id"] == router.DOC_IDS[0]


def test_score_prefix_tracks_any_all_and_intrusion() -> None:
    question = {"expected_document_ids": ["doc-a"], "expected_sources": [{"document_id": "doc-a", "article_type": "normal", "article_no": "1"}]}
    ranks = [{"document_id": "doc-b", "document_source_key": "doc-b/normal/1"}, {"document_id": "doc-a", "document_source_key": "doc-a/normal/1"}]
    score = router._score_prefix(question, ranks, 2)
    assert score["source_any"] is True and score["source_all"] is True
    assert score["document_hit"] is True and score["document_intrusion"] == 0.5


def test_paired_change_preserves_ids() -> None:
    rows = [{"question": {"id": "q1"}, "variants": {"B0": {"metrics": {"5": {"source_any": False, "source_all": False, "document_hit": False}}}, "R1": {"metrics": {"5": {"source_any": True, "source_all": False, "document_hit": True}}}}},
            {"question": {"id": "q2"}, "variants": {"B0": {"metrics": {"5": {"source_any": True, "source_all": True, "document_hit": True}}}, "R1": {"metrics": {"5": {"source_any": False, "source_all": False, "document_hit": False}}}}}]
    assert router._paired(rows, "R1", "5", "source_any")["improved"]["ids"] == ["q1"]
    assert router._paired(rows, "R1", "5", "source_any")["regressed"]["ids"] == ["q2"]
