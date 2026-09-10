"""Offline M10E-B holdout-benchmark contract tests. No test here calls
OpenAI, opens production Chroma (or any real Chroma at all), or touches the
network - mirrors the "no real run happens without explicit opt-in" gate
enforced by `evaluate_m10e_holdout._real_run_opt_in`.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from src import config
from src import evaluate_m10e_holdout as run
from src import m10e_holdout as h


def _row(
    qid: str, dataset: str, *, any1=False, any3=False, any5=False, all1=False, all3=False, all5=False,
    leg1=True, expected_sources=("k1",), top1_legislation=None,
) -> dict:
    return {
        "id": qid, "dataset": dataset, "question": "q", "case_type": "paraphrase", "difficulty": "easy",
        "expected_sources": set(expected_sources), "expected_legislations": {dataset},
        "any_source_hit_at_1": any1, "any_source_hit_at_3": any3, "any_source_hit_at_5": any5,
        "all_sources_match_at_1": all1, "all_sources_match_at_3": all3, "all_sources_match_at_5": all5,
        "expected_legislation_hit_at_1": leg1, "expected_legislation_hit_at_3": leg1, "expected_legislation_hit_at_5": leg1,
        "top1_legislation": top1_legislation or dataset, "non_expected_legislation_count_at_5": 0,
        "non_expected_legislation_share_at_5": 0.0,
        "ranks": [{"rank": 1, "chunk_id": "c1", "qualified_source_key": "k1", "legislation_number": dataset}],
        "expected_source_ranks": {"k1": 1},
    }


# ============================================================================
# Frozen-holdout preflight
# ============================================================================


def test_verify_frozen_holdout_matches_real_file() -> None:
    digest, questions = run.verify_frozen_holdout()
    assert len(digest) == 64
    assert all(c in "0123456789abcdef" for c in digest)
    assert len(questions) == 30


def test_verify_frozen_holdout_detects_tamper(tmp_path) -> None:
    raw = json.loads(h.FINAL_PATH.read_text(encoding="utf-8"))
    raw[0]["gold_human_approved"] = False
    path = tmp_path / "tampered.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(h.HoldoutConstructionError):
        run.verify_frozen_holdout(path)


def test_load_holdout_question_dicts_shape() -> None:
    questions = run.load_holdout_question_dicts()
    assert len(questions) == 30
    ids = [q["id"] for q in questions]
    assert len(set(ids)) == 30
    for q in questions:
        assert isinstance(q["expected_sources"], list) and q["expected_sources"]
        assert isinstance(q["expected_legislations"], list) and q["expected_legislations"]
        assert q["dataset"] in ("5326", "4458")
    per_law = {"5326": 0, "4458": 0}
    for q in questions:
        per_law[q["dataset"]] += 1
    assert per_law == {"5326": 10, "4458": 20}
    distinct_keys = {k for q in questions for k in q["expected_sources"]}
    assert len(distinct_keys) == 35


# ============================================================================
# Experimental-copy-only access (never production)
# ============================================================================


def test_refuses_to_open_production_path_as_copy(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "CHROMA_PATH", str(tmp_path))
    with pytest.raises(run.HoldoutBenchmarkError, match="production"):
        run.open_experimental_copy_collection(tmp_path)


def test_refuses_missing_copy_path(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "CHROMA_PATH", "chroma")
    missing = tmp_path / "does_not_exist"
    with pytest.raises(run.HoldoutBenchmarkError, match="not found"):
        run.open_experimental_copy_collection(missing)


# ============================================================================
# Deltas (§8)
# ============================================================================


def test_compute_deltas_identifies_hits_and_misses() -> None:
    b0 = [_row("q1", "4458", any5=False, all5=False), _row("q2", "4458", any5=True, all5=True)]
    b2 = [_row("q1", "4458", any5=True, all5=True), _row("q2", "4458", any5=False, all5=False)]
    deltas = run.compute_deltas(b0, b2)
    assert deltas["ANY@5"]["b0_miss_to_b2_hit"] == ["q1"]
    assert deltas["ANY@5"]["b0_hit_to_b2_miss"] == ["q2"]
    assert deltas["ALL@5"]["b0_miss_to_b2_hit"] == ["q1"]
    assert deltas["ALL@5"]["b0_hit_to_b2_miss"] == ["q2"]


def test_compute_deltas_requires_matching_ids() -> None:
    b0 = [_row("q1", "4458")]
    b2 = [_row("q2", "4458")]
    with pytest.raises(run.HoldoutBenchmarkError):
        run.compute_deltas(b0, b2)


# ============================================================================
# Success gates (§6/§16) - synthetic scenarios
# ============================================================================


def _synthetic_rows(any5_5326_b0, any5_5326_b2, all5_5326_b0, all5_5326_b2,
                     any5_4458_b0, any5_4458_b2, all5_4458_b0, all5_4458_b2,
                     leg1_b0=30, leg1_b2=30) -> tuple[list[dict], list[dict]]:
    def build(n_5326_any_hit, n_5326_all_hit, n_4458_any_hit, n_4458_all_hit, n_leg1):
        rows = []
        for i in range(10):
            rows.append(_row(f"h5326-{i:02d}", "5326", any5=i < n_5326_any_hit, all5=i < n_5326_all_hit,
                              leg1=(len(rows) < n_leg1)))
        for i in range(20):
            idx = 10 + i
            rows.append(_row(f"h4458-{i:02d}", "4458", any5=i < n_4458_any_hit, all5=i < n_4458_all_hit,
                              leg1=(idx < n_leg1)))
        return rows

    b0 = build(any5_5326_b0, all5_5326_b0, any5_4458_b0, all5_4458_b0, leg1_b0)
    b2 = build(any5_5326_b2, all5_5326_b2, any5_4458_b2, all5_4458_b2, leg1_b2)
    return b0, b2


def test_gates_pass_when_b2_strictly_better() -> None:
    b0, b2 = _synthetic_rows(5, 8, 5, 8, 10, 15, 8, 12)
    result = run.evaluate_gates(b0, b2)
    assert result["decision"] == "VALIDATED"
    assert all(g["pass"] for g in result["gates"].values())


def test_gate_a_fails_on_5326_regression() -> None:
    b0, b2 = _synthetic_rows(8, 5, 8, 5, 10, 15, 8, 12)  # 5326 ANY@5/ALL@5 regress
    result = run.evaluate_gates(b0, b2)
    assert result["gates"]["A_5326_preservation"]["pass"] is False
    assert result["decision"] == "NOT VALIDATED"


def test_gate_b_fails_when_4458_neither_metric_improves() -> None:
    b0, b2 = _synthetic_rows(5, 5, 8, 8, 10, 10, 8, 8)  # 4458 unchanged, no improvement
    result = run.evaluate_gates(b0, b2)
    assert result["gates"]["B_4458_improves_without_material_degradation"]["pass"] is False


def test_gate_b_fails_on_material_degradation() -> None:
    # ANY@5 improves but ALL@5 drops by 3 (> 1 allowed)
    b0, b2 = _synthetic_rows(5, 5, 8, 8, 10, 15, 10, 7)
    result = run.evaluate_gates(b0, b2)
    assert result["gates"]["B_4458_improves_without_material_degradation"]["pass"] is False


def test_gate_b_tolerates_one_question_degradation() -> None:
    b0, b2 = _synthetic_rows(5, 5, 8, 8, 10, 15, 10, 9)  # ALL@5 drops by exactly 1: tolerated
    result = run.evaluate_gates(b0, b2)
    assert result["gates"]["B_4458_improves_without_material_degradation"]["pass"] is True


def test_gate_d_fails_on_legislation_regression() -> None:
    b0, b2 = _synthetic_rows(5, 5, 8, 8, 10, 15, 8, 12, leg1_b0=30, leg1_b2=27)
    result = run.evaluate_gates(b0, b2)
    assert result["gates"]["D_legislation_hit_at_1"]["pass"] is False


# ============================================================================
# Multi-source rows / diagnostics
# ============================================================================


def test_multi_source_rows_filters_by_expected_source_count() -> None:
    rows = [_row("a", "4458", expected_sources=("k1",)), _row("b", "4458", expected_sources=("k1", "k2"))]
    assert [r["id"] for r in run.multi_source_rows(rows)] == ["b"]


def test_multi_source_diagnostics_only_reports_requested_ids() -> None:
    b0 = [_row("h5326-10", "5326", any5=True, all5=False)]
    b2 = [_row("h5326-10", "5326", any5=True, all5=True)]
    out = run.multi_source_diagnostics(("h5326-10", "not-present"), b0, b2)
    assert set(out) == {"h5326-10"}
    assert out["h5326-10"]["b0_all_at_5"] is False
    assert out["h5326-10"]["b2_all_at_5"] is True


# ============================================================================
# Report writers (tmp_path only - never the real reports/ directory)
# ============================================================================


def test_load_holdout_question_dicts_are_json_serializable() -> None:
    """Regression: expected_sources/expected_legislations must be plain
    lists, never bare `set`s, or json.dumps crashes AFTER all real dense
    calls have already been billed (see the first real-run attempt)."""
    questions = run.load_holdout_question_dicts()
    json.dumps(questions)  # must not raise TypeError: Object of type set is not JSON serializable
    for q in questions:
        assert isinstance(q["expected_sources"], list)
        assert isinstance(q["expected_legislations"], list)


def test_write_json_report_survives_a_stray_set(tmp_path) -> None:
    """Defense in depth: even if a `set` slips into a report value, the
    writer must not crash (the primary fix is upstream, this is the net)."""
    path = tmp_path / "r.json"
    run.write_json_report({"weird": {"a", "b", "c"}}, path)
    assert json.loads(path.read_text(encoding="utf-8"))["weird"] == ["a", "b", "c"]


def test_write_json_and_csv_and_md_reports(tmp_path) -> None:
    b0 = [_row("h5326-01", "5326"), _row("h4458-01", "4458")]
    b2 = [_row("h5326-01", "5326", any5=True, all5=True), _row("h4458-01", "4458")]
    summaries = run.build_summaries(b0, b2)
    gate_evaluation = run.evaluate_gates(b0, b2)
    report = {
        "metadata": {"holdout_sha256": "0" * 64, "git_head": "deadbeef", "experimental_copy_path": str(tmp_path)},
        "attempt_history": {
            "execution_attempts_total": 2, "prior_failed_attempts": list(run.PRIOR_FAILED_ATTEMPTS),
            "current_attempt": 2, "valid_benchmark_attempt": 2, "current_attempt_status": "completed",
            "current_attempt_dense_calls": 2, "total_dense_calls_across_all_attempts": 32,
        },
        "summaries": summaries, "gate_evaluation": gate_evaluation,
    }
    json_path, csv_path, md_path = tmp_path / "r.json", tmp_path / "r.csv", tmp_path / "r.md"
    run.write_json_report(report, json_path)
    run.write_csv_report(b0, b2, csv_path)
    run.write_md_report(report, md_path)
    assert json.loads(json_path.read_text(encoding="utf-8"))["gate_evaluation"]["decision"] in ("VALIDATED", "NOT VALIDATED")
    assert csv_path.exists() and csv_path.stat().st_size > 0
    assert "Final decision" in md_path.read_text(encoding="utf-8")


def test_md_report_table_header_matches_column_order() -> None:
    """Regression: the header row must label columns in the SAME order the
    data loop actually fills them - a mismatched header silently produced
    correct underlying numbers under wrong labels (caught by manual JSON
    cross-check after the replacement holdout run)."""
    b0 = [_row("h5326-01", "5326", any1=True), _row("h4458-01", "4458", any1=False)]
    b2 = [_row("h5326-01", "5326", any1=True), _row("h4458-01", "4458", any1=True)]
    summaries = run.build_summaries(b0, b2)
    report = {
        "metadata": {"holdout_sha256": "0" * 64, "git_head": "deadbeef", "experimental_copy_path": "x"},
        "attempt_history": {
            "execution_attempts_total": 1, "prior_failed_attempts": (), "current_attempt": 1,
            "valid_benchmark_attempt": 1, "current_attempt_status": "completed",
            "current_attempt_dense_calls": 2, "total_dense_calls_across_all_attempts": 2,
        },
        "summaries": summaries, "gate_evaluation": run.evaluate_gates(b0, b2),
    }
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "r.md"
        run.write_md_report(report, path)
        text = path.read_text(encoding="utf-8")
    header = next(line for line in text.splitlines() if line.startswith("| Metric"))
    any1_row = next(line for line in text.splitlines() if line.startswith("| ANY@1"))
    header_cols = [c.strip() for c in header.split("|")[1:-1]]
    value_cols = [c.strip() for c in any1_row.split("|")[1:-1]]
    # B0 5326 ANY@1 must be 100% (the only hit for that (strategy, law) pair)
    # and it must sit under the "B0 5326" header, not "B2 5326".
    assert header_cols[1] == "B0 5326"
    assert value_cols[1] == "100.0%"
    assert header_cols[2] == "B2 5326"
    assert value_cols[2] == "100.0%"
    assert header_cols[3] == "B0 4458"
    assert value_cols[3] == "0.0%"
    assert header_cols[4] == "B2 4458"
    assert value_cols[4] == "100.0%"


# ============================================================================
# Real-run gate + no-second-run guard
# ============================================================================


def test_real_run_requires_opt_in(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "OPENAI_API_KEY", None)
    monkeypatch.delenv("RUN_OPENAI_INTEGRATION_TESTS", raising=False)
    with pytest.raises(run.HoldoutBenchmarkError, match="Requires OPENAI_API_KEY"):
        run.main()


def test_module_never_imports_openai_at_module_scope() -> None:
    assert "OpenAI" not in run.__dict__
    assert "openai" not in run.__dict__


def test_existing_output_refuses_second_run(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The exclusive-create guard must fire BEFORE any network code runs -
    this never needs to fake OpenAI at all."""
    monkeypatch.setattr(config, "OPENAI_API_KEY", "sk-fake-for-gate-check-only")
    monkeypatch.setenv("RUN_OPENAI_INTEGRATION_TESTS", "1")
    existing = tmp_path / "already-there.json"
    existing.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(run, "OUTPUT_JSON", existing)
    with pytest.raises(run.HoldoutBenchmarkError, match="already exists"):
        run.main()


def _fake_documents(n: int = 6) -> list:
    return [
        run.e.Document(
            f"c{i}", f"gümrük metni {i}",
            {"legislation_number": "4458" if i % 2 == 0 else "5326", "article_type": "normal", "article_no": str(i)},
        )
        for i in range(1, n + 1)
    ]


def _fake_dense_payload(docs: list):
    chunks = [
        SimpleNamespace(rank=i + 1, chunk_id=d.id, text=d.text, metadata=d.metadata, distance=float(i))
        for i, d in enumerate(docs)
    ]
    return SimpleNamespace(results=chunks, embedding_usage=SimpleNamespace(total_tokens=7), latency_ms=1.5)


class _FakeOpenAIClient:
    """Fake context manager standing in for `openai.OpenAI(...)` - never a
    real client, never reaches the network."""

    def __init__(self, **_kwargs) -> None:
        pass

    def __enter__(self):
        return object()

    def __exit__(self, *_exc) -> bool:
        return False


def test_crash_midloop_preserves_checkpointed_results(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A failure partway through the 30-question loop must NOT erase the
    questions already scored before it - the whole point of checkpointing
    after every dense call. Fully mocked: no OpenAI, no Chroma, no network."""
    docs = _fake_documents()
    inventory = {
        "total": 329, "counts": {"5326": 53, "4458": 276}, "ids": [d.id for d in docs],
        "content_sha256": "fake-for-test", "fingerprint_scope": "test double, not real corpus",
    }
    monkeypatch.setattr(run.e, "snapshot", lambda collection: (docs, dict(inventory)))
    monkeypatch.setattr(run, "open_experimental_copy_collection", lambda copy_path=run.DEFAULT_COPY_PATH: (object(), object()))

    call_count = {"n": 0}

    def fake_collect_dense(query, *, collection, client):
        call_count["n"] += 1
        if call_count["n"] == 3:
            raise RuntimeError("simulated failure after 2 real questions were already scored")
        return _fake_dense_payload(docs)

    monkeypatch.setattr(run.e, "collect_dense", fake_collect_dense)

    import openai
    monkeypatch.setattr(openai, "OpenAI", _FakeOpenAIClient)
    monkeypatch.setattr(config, "OPENAI_API_KEY", "sk-fake-for-gate-check-only")
    monkeypatch.setenv("RUN_OPENAI_INTEGRATION_TESTS", "1")

    output_path = tmp_path / "checkpoint-test.json"
    monkeypatch.setattr(run, "OUTPUT_JSON", output_path)

    with pytest.raises(RuntimeError, match="simulated failure after 2 real questions"):
        run.main()

    assert output_path.exists(), "checkpoint file must exist even though the run crashed"
    saved = json.loads(output_path.read_text(encoding="utf-8"))
    assert saved["metadata"]["status"] == "failed_no_retry"
    assert saved["metadata"]["error_type"] == "RuntimeError"
    assert saved["metadata"]["dense_retrieval_calls"] == 2
    assert len(saved["results"]["B0"]) == 2
    assert len(saved["results"]["B2"]) == 2
    assert {r["id"] for r in saved["results"]["B0"]} == {"h5326-01", "h5326-02"}
    # No second attempt is possible while this file exists.
    with pytest.raises(run.HoldoutBenchmarkError, match="already exists"):
        run.main()


def test_main_honors_explicit_and_env_copy_path_override(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A replacement run must be able to target a freshly created copy
    path (e.g. `.m10e_holdout_chroma_retry1/`) without ever falling back to
    `DEFAULT_COPY_PATH` - and must record that exact path in the report."""
    docs = _fake_documents()
    inventory = {"total": 329, "counts": {"5326": 53, "4458": 276}, "ids": [d.id for d in docs],
                 "content_sha256": "fake", "fingerprint_scope": "test"}
    monkeypatch.setattr(run.e, "snapshot", lambda collection: (docs, dict(inventory)))

    seen_paths = []

    def fake_open(copy_path=run.DEFAULT_COPY_PATH):
        seen_paths.append(Path(copy_path))
        return object(), object()

    monkeypatch.setattr(run, "open_experimental_copy_collection", fake_open)
    monkeypatch.setattr(run.e, "collect_dense", lambda query, *, collection, client: _fake_dense_payload(docs))

    import openai
    monkeypatch.setattr(openai, "OpenAI", _FakeOpenAIClient)
    monkeypatch.setattr(config, "OPENAI_API_KEY", "sk-fake-for-gate-check-only")
    monkeypatch.setenv("RUN_OPENAI_INTEGRATION_TESTS", "1")

    # main() derives the CSV/MD paths from OUTPUT_JSON dynamically (see
    # main()'s own comment on this), so overriding OUTPUT_JSON alone must
    # be enough to keep ALL THREE artifacts out of the real reports/ dir.
    retry_path = tmp_path / ".m10e_holdout_chroma_retry1"
    monkeypatch.setattr(run, "OUTPUT_JSON", tmp_path / "explicit-arg.json")
    real_csv = Path("reports") / "evaluation" / "m10e-holdout-b0-vs-b2.csv"
    real_md = Path("reports") / "evaluation" / "m10e-holdout-b0-vs-b2.md"
    real_csv_mtime_before = real_csv.stat().st_mtime_ns if real_csv.exists() else None
    real_md_mtime_before = real_md.stat().st_mtime_ns if real_md.exists() else None

    run.main(copy_path=retry_path)
    assert seen_paths[-1] == retry_path
    assert (tmp_path / "explicit-arg.csv").exists()
    assert (tmp_path / "explicit-arg.md").exists()
    # The real reports/ artifacts (if present from an actual authorized
    # benchmark run) must be untouched by this test - checked by mtime
    # rather than existence, since a real run may legitimately have
    # created them before this test ever executes.
    assert (real_csv.stat().st_mtime_ns if real_csv.exists() else None) == real_csv_mtime_before
    assert (real_md.stat().st_mtime_ns if real_md.exists() else None) == real_md_mtime_before

    monkeypatch.setattr(run, "OUTPUT_JSON", tmp_path / "env-var.json")
    monkeypatch.setenv("M10E_HOLDOUT_COPY_PATH", str(retry_path))
    run.main()
    assert seen_paths[-1] == retry_path

    saved = json.loads((tmp_path / "env-var.json").read_text(encoding="utf-8"))
    assert saved["metadata"]["experimental_copy_path"] == str(retry_path.resolve())
    assert saved["attempt_history"]["execution_attempts_total"] == 2
    assert saved["attempt_history"]["prior_dense_calls"] == 30
    assert saved["attempt_history"]["current_attempt"] == 2
    assert saved["attempt_history"]["valid_benchmark_attempt"] == 2
    assert saved["attempt_history"]["current_attempt_status"] == "completed"
    assert saved["attempt_history"]["total_dense_calls_across_all_attempts"] == 30 + 30
    assert saved["blindness_integrity"]["prior_attempt_results_ever_inspected"] is False
