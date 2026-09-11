"""Offline checks of M12D diagnostic overlap and API failure accounting."""
from types import SimpleNamespace

import pytest

from scripts import run_m12d_three_source as runner
from src import evaluate_documents as ev
from src.source_identity import DocumentSourceKey


def test_partial_coverage_keeps_duplicate_slots_and_intrusion() -> None:
    """Repeated article chunks cannot satisfy the missing second gold source."""
    first = DocumentSourceKey(runner.DOCS["5607"], "normal", "3")
    second = DocumentSourceKey(runner.DOCS["5607"], "normal", "23")
    other = DocumentSourceKey(runner.DOCS["4458"], "normal", "3")
    q = ev.DocumentQuestion("example", "Example?", frozenset((first, second)), frozenset((first.document_id,)))
    ranks = [ev.DocumentRank(i, f"chunk-{i}", key, key.document_id)
             for i, key in enumerate((first, first, other, other, other), 1)]
    result = ev.evaluate_question(q, ranks)
    analysis = runner.analyze(result)
    assert not analysis["A_complete_top5_miss"]
    assert analysis["B_partial_multi_source_miss"]
    assert analysis["C_correct_document_wrong_articles"]
    assert analysis["D_wrong_document_intrusion"]
    assert analysis["madde_3_slots"] == [1, 2]
    assert analysis["missing_sources"] == [str(second)]
    assert result.metrics[2].document_intrusion == 3 / 5
    assert not result.metrics[2].source_all


def test_complete_miss_overlaps_correct_document_and_intrusion() -> None:
    """Correct-document presence does not imply correct-article coverage."""
    gold = DocumentSourceKey(runner.DOCS["5607"], "normal", "16/A")
    wrong_article = DocumentSourceKey(gold.document_id, "normal", "16")
    wrong_document = DocumentSourceKey(runner.DOCS["5326"], "normal", "16")
    q = ev.DocumentQuestion("example", "Example?", frozenset((gold,)), frozenset((gold.document_id,)))
    ranks = [ev.DocumentRank(i, f"chunk-{i}", key, key.document_id)
             for i, key in enumerate((wrong_document, wrong_article), 1)]
    analysis = runner.analyze(ev.evaluate_question(q, ranks))
    assert analysis["A_complete_top5_miss"]
    assert not analysis["B_partial_multi_source_miss"]
    assert analysis["C_correct_document_wrong_articles"]
    assert analysis["D_wrong_document_intrusion"]
    assert not analysis["top1_document_expected"]
    assert analysis["expected_document_top3"]


def test_embedding_failure_is_counted_once_without_retry() -> None:
    """An endpoint failure propagates after exactly one counted attempt."""
    attempts = []

    def fail(**kwargs: object) -> None:
        attempts.append(kwargs)
        raise ConnectionError("offline simulated failure")

    accounting = {"query_embedding_calls": 0, "prompt_tokens": 0, "total_tokens": 0}
    endpoint = runner.CountingEmbeddings(SimpleNamespace(create=fail), accounting, 1536)
    with pytest.raises(ConnectionError, match="simulated"):
        endpoint.create(input=["Example?"], model="test")
    assert len(attempts) == accounting["query_embedding_calls"] == 1
    assert accounting["total_tokens"] == 0
