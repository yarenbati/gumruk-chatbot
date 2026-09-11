from pathlib import Path

from src.annex_ingest import AnnexSourceFile, AnnexUnit, classify_contributors
from src.source_identity import AnnexSourceKey
from scripts.normalize_gumruk_annex_legacy_office import cache_valid, derived_relative_path, valid_normalized_artifact


def _unit(text: str, name: str = "EK 1.doc") -> AnnexUnit:
    source = AnnexSourceFile("gumruk_yonetmeligi", "z.zip", "z", name, name, name, "OLE_COMPOUND_FILE", ".doc")
    return AnnexUnit(AnnexSourceKey.from_label("EK-1"), "EK-1", source, (), text)


def test_derived_paths_are_stable_and_format_specific() -> None:
    digest = "a" * 64
    assert derived_relative_path("EK 10.doc", digest, "DOCX") == "docx/EK_10-aaaaaaaaaaaaaaaa.docx"
    assert derived_relative_path("EK 10.xls", digest, "XLSX") == "xlsx/EK_10-aaaaaaaaaaaaaaaa.xlsx"


def test_cache_requires_tool_version_and_valid_output(tmp_path: Path) -> None:
    output = tmp_path / "docx" / "source.docx"
    output.parent.mkdir()
    output.write_bytes(b"not-ooxml")
    entry = {"conversion_status": "SUCCESS", "normalization_tool_version": "LibreOffice test", "normalized_relative_path": "docx/source.docx", "normalized_format": "DOCX", "normalized_sha256": "bad"}
    assert not cache_valid(entry, tmp_path, "LibreOffice test")
    assert not cache_valid(entry, tmp_path, "LibreOffice other")
    assert not valid_normalized_artifact(output, "DOCX")


def test_cache_accepts_structurally_valid_xlsx(tmp_path: Path) -> None:
    import hashlib
    import zipfile

    output = tmp_path / "xlsx" / "source.xlsx"
    output.parent.mkdir()
    with zipfile.ZipFile(output, "w") as package:
        package.writestr("xl/workbook.xml", "<workbook/>")
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    entry = {"conversion_status": "SUCCESS", "normalization_tool_version": "LibreOffice test", "normalized_relative_path": "xlsx/source.xlsx", "normalized_format": "XLSX", "normalized_sha256": digest}
    assert valid_normalized_artifact(output, "XLSX")
    assert cache_valid(entry, tmp_path, "LibreOffice test")


def test_multi_source_classification_is_fail_closed_and_deterministic() -> None:
    assert classify_contributors([_unit("same"), _unit("same", "EK 1-alt.doc")]) == "EXACT_DUPLICATE"
    assert classify_contributors([_unit("same text"), _unit(" same   text ", "EK 1-alt.doc")]) == "WHITESPACE_EQUIVALENT"
    assert classify_contributors([_unit("old version"), _unit("new version", "EK 1-alt.doc")]) == "CONFLICTING"
    assert classify_contributors([_unit("form"), _unit("Mülga:RG-1/1/2020", "EK 1-alt.doc")]) == "COMPLEMENTARY"
