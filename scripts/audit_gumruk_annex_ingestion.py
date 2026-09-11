"""Offline M13B-2 audit for logical annex ingestion."""
from __future__ import annotations

import json
import re
import sys
import argparse
from collections import Counter
import re
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from docx import Document

from src.annex_ingest import AnnexSourceFile, NormalizationProvenance, classify_contributors, detect_file_type, ingest_archive, ingest_member, sha256_bytes, conservative_whitespace_hash
from src.source_identity import AnnexSourceKey

ROOT = Path(__file__).resolve().parents[1]
ZIP_PATH = ROOT / "data/raw/gumruk-yonetmeligi-ekler.zip"
MANIFEST_PATH = ROOT / "data/processed/gumruk-yonetmeligi-annex-normalized/normalization-manifest.json"
REF_RE = re.compile(r"\bEK\s*[-–—]?\s*(\d{1,3})(?:\s*[/–—-]\s*([A-Za-zÇĞİÖŞÜçğıöşü]))?\b", re.I)


def key_order(key: AnnexSourceKey) -> tuple[str, int, str]:
    """Sort base annexes before lettered sub-annexes deterministically."""
    return key.document_id, key.annex_no, key.annex_subpart or ""


def main_reference_keys() -> set[AnnexSourceKey]:
    """Reuse the admitted main DOCX as the source of normalized EK references."""
    document = Document(str(ROOT / "data/raw/gumruk-yonetmeligi.docx"))
    text = "\n".join(p.text for p in document.paragraphs)
    return {AnnexSourceKey("gumruk_yonetmeligi", int(m.group(1)), m.group(2).upper() if m.group(2) else None) for m in REF_RE.finditer(text)}


def raw_multi_source_inventory() -> dict[str, list[dict[str, object]]]:
    """Return per-contributor hashes and structure before canonical aggregation."""
    manifest = {}
    if MANIFEST_PATH.exists():
        manifest = {x["archive_member_path"]: x for x in json.loads(MANIFEST_PATH.read_text(encoding="utf-8")).get("entries", [])}
    groups: dict[str, list[dict[str, object]]] = {}
    with zipfile.ZipFile(ZIP_PATH) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            original = archive.read(info)
            entry = manifest.get(info.filename)
            data = original
            normalization = None
            if entry and entry.get("conversion_status") == "SUCCESS":
                data = (MANIFEST_PATH.parent / entry["normalized_relative_path"]).read_bytes()
                normalization = NormalizationProvenance(entry["normalization_tool"], entry["normalization_tool_version"], entry["normalization_command_family"], entry["normalized_relative_path"], entry["normalized_sha256"])
            source = AnnexSourceFile("gumruk_yonetmeligi", str(ZIP_PATH.relative_to(ROOT)), sha256_bytes(ZIP_PATH.read_bytes()), info.filename, Path(info.filename).name, sha256_bytes(original), detect_file_type(original), Path(info.filename).suffix.lower(), normalization)
            for unit in ingest_member(data, info.filename, source=source):
                if unit.source_key.label not in groups:
                    groups[unit.source_key.label] = []
                groups[unit.source_key.label].append({"archive_member_filename": info.filename, "archive_member_sha256": source.archive_member_sha256, "normalized_sha256": normalization.normalized_sha256 if normalization else None, "block_count": len(unit.blocks), "paragraph_blocks": sum(block.kind == "paragraph" for block in unit.blocks), "table_blocks": sum(block.kind == "table" for block in unit.blocks), "spreadsheet_blocks": sum(block.kind == "spreadsheet" for block in unit.blocks), "rendered_text_length": len(unit.rendered_text), "rendered_text_sha256": sha256_bytes(unit.rendered_text.encode("utf-8")), "normalized_comparison_sha256": conservative_whitespace_hash(unit.rendered_text), "unit": unit})
    return {key: values for key, values in groups.items() if len(values) > 1}


def write_processed_corpus(units: list[object], diagnostics: dict[str, object]) -> Path:
    """Write the complete ignored derived corpus with stable UTF-8 newlines."""
    output = ROOT / "data/processed/gumruk-yonetmeligi-annexes.json"
    payload = {"schema_version": 1, "source_zip_sha256": sha256_bytes(ZIP_PATH.read_bytes()), "normalization_manifest": str(MANIFEST_PATH.relative_to(ROOT)), "diagnostics": diagnostics,
               "units": [unit.to_dict() for unit in sorted(units, key=lambda unit: (unit.source_key.document_id, unit.source_key.annex_no, unit.source_key.annex_subpart or ""))]}
    with output.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return output


def run(write_corpus: bool = False) -> dict[str, object]:
    """Run the audit without creating a processed corpus or external state."""
    units, diagnostics = ingest_archive(ZIP_PATH, normalization_manifest=MANIFEST_PATH if MANIFEST_PATH.exists() else None)
    raw_groups = raw_multi_source_inventory()
    keys = {u.source_key for u in units}
    refs = main_reference_keys()
    resolved = refs & keys
    base = {AnnexSourceKey("gumruk_yonetmeligi", n) for n in range(1, 84)}
    reps = {f"EK-{n}": [{"member": u.source_member.archive_member_filename, "detected": u.source_member.detected_file_type,
                         "reader_warnings": list(u.warnings), "logical_keys": [str(v.source_key) for v in units if v.source_member.archive_member_path == u.source_member.archive_member_path],
                         "paragraph_blocks": sum(b.kind == "paragraph" for b in u.blocks), "table_blocks": sum(b.kind == "table" for b in u.blocks),
                         "spreadsheet_blocks": sum(b.kind == "spreadsheet" for b in u.blocks), "rendered_text_length": len(u.rendered_text),
                         "provenance_complete": bool(u.source_member.archive_member_sha256 and u.source_member.source_zip_sha256)}
                        for u in units if u.source_key.annex_no == n] for n in (7, 10, 48, 62, 70, 77, 81, 83)}
    multi_source_units = [unit for unit in units if unit.multi_source_relationship]
    relationship_counts = Counter(unit.multi_source_relationship for unit in multi_source_units)
    canonical_contributors = {str(unit.source_key): (unit.canonical_source_member.archive_member_path if unit.canonical_source_member else unit.source_member.archive_member_path) for unit in multi_source_units}
    normalization = {}
    if MANIFEST_PATH.exists():
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        paths = [entry.get("normalized_relative_path") for entry in manifest.get("entries", [])]
        normalization = {"normalization_manifest": str(MANIFEST_PATH.relative_to(ROOT)), "normalization_tool": manifest.get("normalization_tool"), "normalization_tool_version": manifest.get("normalization_tool_version"), "normalization_statuses": {status: sum(entry.get("conversion_status") == status for entry in manifest.get("entries", [])) for status in sorted({entry.get("conversion_status") for entry in manifest.get("entries", [])})}, "normalization_provenance_complete": all(entry.get("conversion_status") == "SUCCESS" and entry.get("normalized_sha256") for entry in manifest.get("entries", [])), "normalization_output_path_collisions": sorted({path for path in paths if paths.count(path) > 1})}
    if write_corpus:
        write_processed_corpus(units, diagnostics)
    inventory = {key: [{field: value for field, value in contributor.items() if field != "unit"} for contributor in values] for key, values in raw_groups.items()}
    report = {**diagnostics, **normalization, "multi_source_logical_annex_count": len(multi_source_units), "relationship_classification_counts": {name: relationship_counts.get(name, 0) for name in ("EXACT_DUPLICATE", "WHITESPACE_EQUIVALENT", "STRUCTURALLY_EQUIVALENT", "COMPLEMENTARY", "CONFLICTING", "UNKNOWN")}, "multi_source_inventory": inventory, "canonical_contributors": canonical_contributors, "duplicate_content_suppressed_count": sum(len(unit.source_members) - 1 for unit in multi_source_units if unit.multi_source_relationship in {"EXACT_DUPLICATE", "WHITESPACE_EQUIVALENT", "STRUCTURALLY_EQUIVALENT"}), "complementary_merge_count": relationship_counts.get("COMPLEMENTARY", 0), "conflict_count": relationship_counts.get("CONFLICTING", 0), "unknown_count": relationship_counts.get("UNKNOWN", 0), "base_coverage": len(base & keys), "missing_base": [str(k) for k in sorted(base - keys)],
              "sub_annexes": [str(k) for k in sorted(keys, key=key_order) if k.annex_subpart], "sub_annex_count": sum(k.annex_subpart is not None for k in keys),
              "main_reference_total": len(refs), "main_reference_resolved": len(resolved), "main_reference_unresolved": [str(k) for k in sorted(refs - keys, key=key_order)],
              "processed_corpus_status": ("COMPLETE_DERIVED_CORPUS_PRESENT" if (ROOT / "data/processed/gumruk-yonetmeligi-annexes.json").exists() else "NOT_CREATED"), "representative": reps}
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-corpus", action="store_true")
    run(write_corpus=parser.parse_args().write_corpus)
