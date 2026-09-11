"""Offline invariants for the M13A source admission audit."""

from pathlib import Path

from scripts.audit_gumruk_yonetmeligi_structure import MAIN_PATH, ZIP_PATH, audit_main, audit_zip
from src import source_registry

ROOT = Path(__file__).resolve().parents[1]


def test_admitted_sources_exist_and_zip_is_integral() -> None:
    assert MAIN_PATH.is_file()
    assert ZIP_PATH.is_file()
    result = audit_zip()
    assert result["zip_integrity"] is True
    assert result["entry_count"] == 87
    assert result["zero_byte_files"] == []


def test_main_audit_reports_hierarchy_and_parser_reconstruction() -> None:
    result = audit_main()
    assert result["ooxml_valid"] is True
    assert result["hierarchy_counts"] == {"KİTAP": 12, "KISIM": 33, "BÖLÜM": 22}
    assert result["parser"]["success"] is True
    assert result["parser"]["article_count"] == 524
    assert result["parser"]["chunk_count"] == 526
    assert result["parser"]["reconstruction_failures"] == []


def test_manifest_uses_numberless_canonical_regulation_identity() -> None:
    registry = source_registry.load_manifest(ROOT / "data/source_manifest.json", project_root=ROOT)
    regulation = registry.by_document_id("gumruk_yonetmeligi")
    assert regulation.title == "Gümrük Yönetmeliği"
    assert regulation.legislation_number is None
    assert regulation.local_file == "data/raw/gumruk-yonetmeligi.docx"
