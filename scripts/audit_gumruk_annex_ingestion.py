"""Offline M13B-2 audit for logical annex ingestion."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from docx import Document

from src.annex_ingest import ingest_archive
from src.source_identity import AnnexSourceKey

ROOT = Path(__file__).resolve().parents[1]
ZIP_PATH = ROOT / "data/raw/gumruk-yonetmeligi-ekler.zip"
REF_RE = re.compile(r"\bEK\s*[-–—]?\s*(\d{1,3})(?:\s*[/–—-]\s*([A-Za-zÇĞİÖŞÜçğıöşü]))?\b", re.I)


def key_order(key: AnnexSourceKey) -> tuple[str, int, str]:
    """Sort base annexes before lettered sub-annexes deterministically."""
    return key.document_id, key.annex_no, key.annex_subpart or ""


def main_reference_keys() -> set[AnnexSourceKey]:
    """Reuse the admitted main DOCX as the source of normalized EK references."""
    document = Document(str(ROOT / "data/raw/gumruk-yonetmeligi.docx"))
    text = "\n".join(p.text for p in document.paragraphs)
    return {AnnexSourceKey("gumruk_yonetmeligi", int(m.group(1)), m.group(2).upper() if m.group(2) else None) for m in REF_RE.finditer(text)}


def run() -> dict[str, object]:
    """Run the audit without creating a processed corpus or external state."""
    units, diagnostics = ingest_archive(ZIP_PATH)
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
    report = {**diagnostics, "base_coverage": len(base & keys), "missing_base": [str(k) for k in sorted(base - keys)],
              "sub_annexes": [str(k) for k in sorted(keys, key=key_order) if k.annex_subpart], "sub_annex_count": sum(k.annex_subpart is not None for k in keys),
              "main_reference_total": len(refs), "main_reference_resolved": len(resolved), "main_reference_unresolved": [str(k) for k in sorted(refs - keys, key=key_order)],
              "representative": reps}
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return report


if __name__ == "__main__":
    run()
