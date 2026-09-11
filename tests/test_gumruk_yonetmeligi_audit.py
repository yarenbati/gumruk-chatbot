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
    assert result["provision_counts"] == {
        "article_like_units": 528,
        "plain_numeric_articles": 488,
        "suffixed_articles": 27,
        "temporary_articles": 13,
        "ek_articles": 0,
    }
    assert result["parser"]["article_count"] == 528
    assert result["parser"]["article_type_distribution"] == {"normal": 515, "gecici": 13}
    assert result["parser"]["chunk_count"] == 530
    assert result["unparsed_provision_labels"] == []
    assert result["parser"]["suffix_family_present"] is True
    assert result["document_source_key_validation"] == {
        "tested": 528,
        "errors": [],
        "unique": True,
    }
    assert result["unknown_article_id_count"] == 0
    assert result["unknown_chunk_id_count"] == 0
    assert result["document_id_scoped_storage"] is True
    assert result["parser"]["reconstruction_failures"] == []


def test_manifest_uses_numberless_canonical_regulation_identity() -> None:
    registry = source_registry.load_manifest(ROOT / "data/source_manifest.json", project_root=ROOT)
    regulation = registry.by_document_id("gumruk_yonetmeligi")
    assert regulation.title == "Gümrük Yönetmeliği"
    assert regulation.legislation_number is None
    assert regulation.local_file == "data/raw/gumruk-yonetmeligi.docx"
