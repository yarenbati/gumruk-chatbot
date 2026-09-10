"""Offline structural allocation and frozen-artifact consistency checks."""

from __future__ import annotations

import ast
import random
from pathlib import Path

import pytest

from src import m10e_failure_analysis as analysis


def _ranks(ids: list[str]) -> list[analysis.Row]:
    return [{"chunk_id": cid, "qualified_source_key": "law/normal/" + cid,
             "legislation_number": "law", "rank": i} for i, cid in enumerate(ids, 1)]


def test_anchor_restores_dense_first_without_mutating_inputs() -> None:
    dense, hybrid = _ranks(list("abcde")), _ranks(list("fghij"))
    before = [dict(r) for r in dense + hybrid]
    result = analysis.allocate(dense, hybrid, "C1")
    assert [r["chunk_id"] for r in result] == list("afghi")
    assert dense + hybrid == before
    assert [r["rank"] for r in result] == [1, 2, 3, 4, 5]


def test_alternation_skips_overlap_within_turn_and_keeps_distinct_chunks() -> None:
    dense, hybrid = _ranks(list("abcde")), _ranks(list("acfgb"))
    # Two chunks may have the same source; identity semantics are not changed.
    hybrid[2]["qualified_source_key"] = hybrid[1]["qualified_source_key"]
    result = analysis.allocate(dense, hybrid, "C2")
    assert [r["chunk_id"] for r in result] == list("acbfd")
    assert result[1]["qualified_source_key"] == result[3]["qualified_source_key"]


@pytest.mark.parametrize("strategy", ["C1", "C2"])
def test_saved_top5_is_sufficient_for_full_list_allocation(strategy: str) -> None:
    rng = random.Random(104)
    universe = [str(i) for i in range(40)]
    for _ in range(150):
        dense = _ranks(rng.sample(universe, 20))
        hybrid = _ranks(rng.sample(universe, 30))
        assert analysis.allocate(dense[:5], hybrid[:5], strategy) == analysis.allocate(dense, hybrid, strategy)


def test_insufficient_candidates_and_unknown_strategy_fail_closed() -> None:
    with pytest.raises(ValueError, match="Insufficient"):
        analysis.allocate(_ranks(["a"]), _ranks(["a"]), "C1")
    with pytest.raises(ValueError, match="Unknown"):
        analysis.allocate([], [], "invented")


def test_multisource_and_intrusion_labels_overlap() -> None:
    dense, hybrid = _ranks(list("abcde")), _ranks(list("axfgh"))
    hybrid[1]["legislation_number"] = "other"
    q = {"expected_sources": ["law/normal/a", "law/normal/b"], "expected_legislations": ["law"]}
    assert analysis.classify(q, dense, hybrid) == [
        "DENSE EVIDENCE DISPLACEMENT", "MULTI-SOURCE COMPLETENESS LOSS", "CROSS-LAW INTRUSION"]
    assert analysis.measure(q, hybrid)["cross-law intrusion@5"] == 0.2


def test_replay_agrees_with_frozen_scores_and_preserves_input_bytes() -> None:
    paths = [analysis.ROOT / "reports/evaluation" / (name + ".json") for name in analysis.INPUTS]
    before = [p.read_bytes() for p in paths]
    result = analysis.analyze()
    assert len(result["questions"]) == 105
    assert len({(q["benchmark"], q["id"]) for q in result["questions"]}) == 105
    assert result["development_only"] is True
    assert result["selected_candidate"] is None
    assert before == [p.read_bytes() for p in paths]
    for q in result["questions"]:
        assert q["rankings"]["C1"][0]["chunk_id"] == q["rankings"]["B0"][0]["chunk_id"]
        assert q["rankings"]["C2"][0]["chunk_id"] == q["rankings"]["B0"][0]["chunk_id"]


def test_analysis_has_only_standard_library_imports() -> None:
    tree = ast.parse(Path(analysis.__file__).read_text(encoding="utf-8"))
    imports = {node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    imports.update(alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names)
    assert imports <= {"__future__", "csv", "hashlib", "json", "pathlib", "typing"}
