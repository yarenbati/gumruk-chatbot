"""Offline synthetic tests for copy safety and metadata diagnostics."""
from pathlib import Path
import pytest
from scripts import m11d_metadata_audit as audit
from src import source_registry


@pytest.fixture
def registry(tmp_path):
    return source_registry.SourceRegistry((source_registry.DocumentRecord(
        "5326_kabahatler_kanunu", "Test law", "Kanun", "test.docx", "5326"),), tmp_path)


def row(record_id="5326-test", **changes):
    metadata = dict(document_id="5326_kabahatler_kanunu", legislation_number="5326",
                    article_type="normal", article_no="4", article_id="test-article")
    metadata.update(changes)
    return dict(id=record_id, metadata=metadata)


def test_fresh_copy_exact_and_production_unchanged(tmp_path):
    production = tmp_path / "production"
    production.mkdir()
    (production / "db").write_bytes(b"unchanged bytes")
    before = audit.file_hashes(production)
    copy = tmp_path / "copy"
    assert audit.verified_copy(production, copy) == before
    assert audit.file_hashes(copy) == before == audit.file_hashes(production)
    with pytest.raises(RuntimeError, match="fresh"):
        audit.verified_copy(production, copy)


@pytest.mark.parametrize("relative", [".", "child"])
def test_production_or_nested_copy_rejected(tmp_path, relative):
    with pytest.raises(RuntimeError, match="disjoint"):
        audit.verified_copy(tmp_path, tmp_path / relative)


def test_corrupted_copy_rejected(tmp_path, monkeypatch):
    production = tmp_path / "production"
    production.mkdir()
    (production / "db").write_bytes(b"original")
    def corrupt(src, dst):
        dst.mkdir()
        (dst / "db").write_bytes(b"corrupt")
    monkeypatch.setattr(audit.shutil, "copytree", corrupt)
    with pytest.raises(RuntimeError, match="verification"):
        audit.verified_copy(production, tmp_path / "copy")


def test_multiple_chunks_are_not_collisions(registry):
    result = audit.analyze([row("5326-a"), row("5326-b")], registry)
    assert result["unique_source_keys"] == 1
    assert result["multi_chunk_source_count"] == 1
    assert result["max_chunks_per_source"] == 2
    assert result["issues"] == []
    assert result["record_ids_unique"]


@pytest.mark.parametrize("field,value", [
    ("document_id", None), ("document_id", "BAD"), ("article_type", None),
    ("article_type", "unknown"), ("article_no", None), ("article_no", "42//"),
])
def test_missing_invalid_canonical_fields(registry, field, value):
    result = audit.analyze([row(**{field: value})], registry)
    assert result["valid_canonical_keys"] == 0
    assert result["coverage"][field]["missing" if value is None else "invalid"] == 1
    assert result["compatibility"] == "FAIL"
    assert result["issues"][0]["id"] == "5326-test"


@pytest.mark.parametrize("changes", [{"document_id": "unknown_document"}, {"legislation_number": "4458"}])
def test_manifest_inconsistency(registry, changes):
    assert audit.analyze([row(**changes)], registry)["affected_records"] == 1


def test_duplicate_record_ids_rejected(registry):
    result = audit.analyze([row(), row(article_no="5")], registry)
    assert not result["record_ids_unique"]
    assert result["compatibility"] == "FAIL"


def test_current_prefix_diagnostic(registry):
    result = audit.analyze([row("4458-wrong")], registry)
    assert "prefix" in result["issues"][0]["errors"][0]


def test_inspection_refuses_production_before_client(tmp_path):
    with pytest.raises(RuntimeError, match="production"):
        audit.inspect_copy(tmp_path, tmp_path, None)
