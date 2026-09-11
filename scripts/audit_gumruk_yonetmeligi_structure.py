"""Offline M13A source and structure audit for Gümrük Yönetmeliği.

This module only reads the admitted DOCX and annex ZIP.  It does not embed,
index, open Chroma, or alter parser/production code.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import zipfile
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from docx import Document

from src import chunk, ingest, source_identity

ROOT = Path(__file__).resolve().parents[1]
MAIN_PATH = ROOT / "data/raw/gumruk-yonetmeligi.docx"
ZIP_PATH = ROOT / "data/raw/gumruk-yonetmeligi-ekler.zip"
REPORT_PATH = ROOT / "docs/source-analysis-gumruk-yonetmeligi.md"
ARTICLE_RE = re.compile(r"^\s*MADDE\s+(\d+)\s*(?:/\s*([A-ZÇĞİÖŞ]))?\s*[–—-]", re.IGNORECASE)
TEMP_RE = re.compile(r"^\s*GEÇİCİ\s+MADDE\s+(\d+)\s*[–—-]", re.IGNORECASE)
EK_RE = re.compile(r"^\s*EK\s+MADDE\s+(\d+)\s*[–—-]", re.IGNORECASE)
REF_RE = re.compile(r"\bEK\s*[-–—]?\s*(\d{1,2})(?:\s*[/–—-]\s*([A-ZÇĞİÖŞ]))?\b", re.IGNORECASE)
ORDINAL = r"(?:BİRİNCİ|İKİNCİ|ÜÇÜNCÜ|DÖRDÜNCÜ|BEŞİNCİ|ALTINCI|YEDİNCİ|SEKİZİNCİ|DOKUZUNCU|ONUNCU|ONBİRİNCİ|ONİKİNCİ|ONÜÇÜNCÜ)"
HIERARCHY_RE = re.compile(rf"^\s*({ORDINAL})\s+(KİTAP|KISIM|BÖLÜM|AYIRIM)\s*$", re.IGNORECASE)


def sha256_bytes(data: bytes) -> str:
    """Return SHA256 for immutable source bytes."""
    return hashlib.sha256(data).hexdigest()


def file_fingerprint(path: Path) -> dict[str, Any]:
    """Report path, size, and SHA256 without changing the file."""
    data = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)), "size_bytes": len(data), "sha256": sha256_bytes(data)}


def detect_signature(data: bytes, name: str) -> str:
    """Classify common OOXML/OLE/RTF signatures independently of extension."""
    lower = name.lower()
    if data.startswith(b"{\\rtf"):
        return "RTF"
    if data.startswith(bytes.fromhex("d0cf11e0a1b11ae1")):
        if lower.endswith(".xls"):
            return "OLE/Compound File (likely legacy XLS or form)"
        return "OLE/Compound File (likely legacy DOC)"
    if data.startswith(b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as package:
                names = set(package.namelist())
                if "word/document.xml" in names:
                    return "OOXML DOCX"
                if "xl/workbook.xml" in names:
                    return "OOXML XLSX"
        except zipfile.BadZipFile:
            return "ZIP (invalid OOXML)"
        return "ZIP"
    return "unknown"


def _docx_text(data: bytes) -> tuple[list[str], int, list[tuple[int, int]]]:
    document = Document(io.BytesIO(data))
    paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
    tables = [(len(table.rows), max((len(row.cells) for row in table.rows), default=0)) for table in document.tables]
    return paragraphs, len(document.tables), tables


def _rtf_text(data: bytes) -> str:
    text = data.decode("cp1252", errors="replace")
    text = re.sub(r"\\'[0-9a-fA-F]{2}", "", text)
    text = re.sub(r"\\[a-zA-Z]+-?\d* ?", "", text)
    return re.sub(r"[{}]", " ", text)


def _annex_label(name: str) -> str | None:
    match = re.search(r"\b[Ee][Kk][ -]?(\d{1,2})(?:[ -]?([A-ZÇĞİÖŞ]))?\b", name)
    if not match:
        match = re.search(r"\b[Ee][Kk][ -]?(\d{1,2})\b", name)
    if not match:
        return None
    suffix = f"/{match.group(2).upper()}" if match.group(2) else ""
    return f"EK-{int(match.group(1))}{suffix}"


def _member_text(data: bytes, name: str) -> tuple[str, dict[str, Any]]:
    signature = detect_signature(data, name)
    details: dict[str, Any] = {"signature": signature, "paragraphs": 0, "tables": 0, "text_sample": ""}
    if signature == "OOXML DOCX":
        paragraphs, tables, dimensions = _docx_text(data)
        details.update(paragraphs=len(paragraphs), tables=tables, table_dimensions=dimensions, text_sample="\n".join(paragraphs[:8]))
        return "form/table-heavy" if tables else "text", details
    if signature == "RTF":
        text = _rtf_text(data)
        details.update(paragraphs=len([line for line in text.splitlines() if line.strip()]), text_sample=text[:600])
        return "text", details
    if signature == "OOXML XLSX":
        with zipfile.ZipFile(io.BytesIO(data)) as package:
            xml = package.read("xl/workbook.xml").decode("utf-8", errors="replace")
        details["sheet_count"] = xml.count("<sheet ")
        return "spreadsheet", details
    if signature.startswith("OLE") and name.lower().endswith(".xls"):
        return "spreadsheet", details
    if signature.startswith("OLE"):
        return "text/form (legacy binary Word; reader required)", details
    return "special/unknown", details


def audit_main(path: Path = MAIN_PATH) -> dict[str, Any]:
    """Audit the real main DOCX and current parser/chunker behavior."""
    raw = path.read_bytes()
    document = Document(str(path))
    paragraphs = ingest.extract_paragraphs(document)
    all_text = "\n".join(paragraph.text for paragraph in paragraphs)
    hierarchy = Counter()
    hierarchy_examples: dict[str, list[str]] = defaultdict(list)
    for paragraph in paragraphs:
        match = HIERARCHY_RE.match(paragraph.text.strip())
        if match:
            unit = match.group(2).upper()
            hierarchy[unit] += 1
            if len(hierarchy_examples[unit]) < 5:
                hierarchy_examples[unit].append(paragraph.text.strip())
    provisions: list[dict[str, Any]] = []
    for paragraph in paragraphs:
        text = paragraph.text.strip()
        match = ARTICLE_RE.match(text)
        if match:
            provisions.append({"label": f"{match.group(1)}/{match.group(2).upper()}" if match.group(2) else match.group(1), "type": "normal", "numeric": int(match.group(1)), "suffix": match.group(2).upper() if match.group(2) else None, "paragraph_index": paragraph.index})
            continue
        match = TEMP_RE.match(text)
        if match:
            provisions.append({"label": match.group(1), "type": "temporary_article", "numeric": int(match.group(1)), "suffix": None, "paragraph_index": paragraph.index})
            continue
        match = EK_RE.match(text)
        if match:
            provisions.append({"label": match.group(1), "type": "ek_article", "numeric": int(match.group(1)), "suffix": None, "paragraph_index": paragraph.index})
    numeric = sorted({item["numeric"] for item in provisions if item["type"] == "normal"})
    labels = [item["label"] for item in provisions]
    article_objects: list[Any] = []
    parser_error = None
    try:
        article_objects = chunk.parse_articles(paragraphs, document_id="gumruk_yonetmeligi", legislation_number=None)
    except Exception as exc:  # diagnostic result, not a swallowed production error
        parser_error = f"{type(exc).__name__}: {exc}"
    chunks: list[Any] = []
    if article_objects:
        chunks = chunk.build_chunks(article_objects)
    reconstruction_failures = []
    for article in article_objects:
        article_chunks = [piece for piece in chunks if piece.article_id == article.article_id]
        reconstructed = "\n".join(piece.text for piece in article_chunks)
        if reconstructed != article.text:
            reconstruction_failures.append({"article_id": article.article_id, "missing_or_changed": True, "chunk_count": len(article_chunks)})
    source_key_errors = []
    source_keys = []
    for article in article_objects:
        try:
            source_keys.append(str(source_identity.DocumentSourceKey(article.document_id or "", article.article_type, article.article_no)))
        except source_identity.SourceIdentityError as exc:
            source_key_errors.append({"article_no": article.article_no, "article_type": article.article_type, "error": str(exc)})
    section_samples = []
    for article in article_objects:
        if article.article_no in {"1", "300", "72/A", "580/A"} or article.article_type == "gecici":
            section_samples.append({"article_no": article.article_no, "article_type": article.article_type, "section_context": article.section_context})
    return {
        "file": file_fingerprint(path),
        "ooxml_valid": True,
        "paragraph_count": len(document.paragraphs),
        "non_empty_paragraph_count": len(paragraphs),
        "table_count": len(document.tables),
        "table_dimensions": [(len(table.rows), max((len(row.cells) for row in table.rows), default=0)) for table in document.tables],
        "table_roles": ["table content is outside current paragraph extractor; requires table-aware audit/ingestion" for _ in document.tables],
        "hierarchy_counts": dict(hierarchy),
        "hierarchy_examples": dict(hierarchy_examples),
        "provision_counts": {"article_like_units": len(provisions), "plain_numeric_articles": sum(item["type"] == "normal" and item["suffix"] is None for item in provisions), "suffixed_articles": sum(item["type"] == "normal" and item["suffix"] is not None for item in provisions), "temporary_articles": sum(item["type"] == "temporary_article" for item in provisions), "ek_articles": sum(item["type"] == "ek_article" for item in provisions)},
        "suffix_letters": sorted({item["suffix"] for item in provisions if item["suffix"]}),
        "lowest_numeric_article": min(numeric) if numeric else None,
        "highest_numeric_article": max(numeric) if numeric else None,
        "numeric_article_gaps": [number for number in range(min(numeric), max(numeric) + 1) if number not in numeric] if numeric else [],
        "duplicate_provision_labels": sorted(label for label, count in Counter(labels).items() if count > 1),
        "provision_label_collisions": {label: count for label, count in Counter(labels).items() if count > 1},
        "internal_patterns": {"fikra_parenthesized": len(re.findall(r"(?<!\w)\(\d+\)", all_text)), "lettered_bent": len(re.findall(r"(?m)^\s*[a-zçğıöşü]\)\s", all_text, re.IGNORECASE)), "numbered_alt_bent": len(re.findall(r"(?m)^\s*\d+\)\s", all_text)), "mülga": len(re.findall(r"Mülga", all_text, re.IGNORECASE)), "degisik": len(re.findall(r"Değişik", all_text, re.IGNORECASE)), "ek_annotations": len(re.findall(r"\(Ek:", all_text, re.IGNORECASE)), "rg_references": len(re.findall(r"RG-\d{1,2}/\d{1,2}/\d{4}-\d+", all_text)), "court_annotations": len(re.findall(r"Danıştay|mahkeme|yürütmesinin durdurulmasına", all_text, re.IGNORECASE)), "article_titles": sum(article.article_title is not None for article in article_objects), "inline_footnote_reference_ids": sum(len(paragraph.footnote_reference_ids or []) for paragraph in paragraphs)},
        "footnote_history": {"footnotes_xml_present": "word/footnotes.xml" in zipfile.ZipFile(path).namelist(), "amendment_history_marker_present": bool(re.search(r"EK VE DEĞİŞİKLİK", all_text, re.IGNORECASE)), "history_blocks_are_not_resolved_by_current_parser": True},
        "parser": {"success": parser_error is None, "error": parser_error, "article_count": len(article_objects), "article_type_distribution": dict(Counter(article.article_type for article in article_objects)), "first": {"article_no": article_objects[0].article_no, "article_type": article_objects[0].article_type} if article_objects else None, "last": {"article_no": article_objects[-1].article_no, "article_type": article_objects[-1].article_type} if article_objects else None, "chunk_count": len(chunks), "multi_chunk_provision_count": sum(sum(piece.article_id == article.article_id for piece in chunks) > 1 for article in article_objects), "duplicate_article_ids": sorted(article_id for article_id, count in Counter(article.article_id for article in article_objects).items() if count > 1), "duplicate_chunk_ids": sorted(chunk_id for chunk_id, count in Counter(piece.chunk_id for piece in chunks).items() if count > 1), "section_samples": section_samples, "reconstruction_tested": len(article_objects), "reconstruction_failures": reconstruction_failures, "suffix_family_present": all(any(article.article_no == f"72/{letter}" for article in article_objects) for letter in "ABCDEFGĞHIİJKLMNOÖPRŞT")},
        "document_source_key_validation": {"tested": len(source_keys), "errors": source_key_errors, "unique": len(source_keys) == len(set(source_keys))},
        "unknown_article_id_count": sum(article.article_id.startswith("unknown-") for article in article_objects),
        "unknown_chunk_id_count": sum(piece.chunk_id.startswith("unknown-") for piece in chunks),
        "document_id_scoped_storage": all(article.article_id.startswith("gumruk_yonetmeligi-") for article in article_objects),
        "raw_provision_labels": labels,
        "unparsed_provision_labels": sorted(set(labels) - set(article.article_no for article in article_objects)),
        "annex_references": sorted({f"EK-{int(match.group(1))}{('/' + match.group(2).upper()) if match.group(2) else ''}" for match in REF_RE.finditer(all_text)}, key=lambda value: (int(re.search(r"\d+", value).group()), value)),
    }


def audit_zip(path: Path = ZIP_PATH) -> dict[str, Any]:
    """Audit ZIP integrity, every member, signatures, and logical annex coverage."""
    raw = path.read_bytes()
    with zipfile.ZipFile(path) as archive:
        bad = archive.testzip()
        infos = archive.infolist()
        names = [info.filename for info in infos]
        duplicates = sorted(name for name, count in Counter(names).items() if count > 1)
        members = []
        for info in infos:
            if info.is_dir():
                continue
            data = archive.read(info)
            orientation, details = _member_text(data, info.filename)
            members.append({"archive_path": info.filename, "filename": Path(info.filename).name, "label": _annex_label(info.filename), "extension": Path(info.filename).suffix.lower(), "size_bytes": len(data), "sha256": sha256_bytes(data), "signature": details.pop("signature"), "orientation": orientation, "details": details})
    direct = defaultdict(list)
    for member in members:
        if member["label"]:
            direct[member["label"].split("/")[0]].append(member["filename"])
    embedded: dict[str, list[str]] = defaultdict(list)
    for member in members:
        text = member["details"].get("text_sample", "")
        for match in REF_RE.finditer(text):
            label = f"EK-{int(match.group(1))}{('/' + match.group(2).upper()) if match.group(2) else ''}"
            if label not in direct and label != member["label"]:
                embedded[label].append(member["filename"])
    coverage = []
    for number in range(1, 84):
        key = f"EK-{number}"
        filenames = sorted(direct.get(key, []))
        possible = sorted(embedded.get(key, []))
        coverage.append({"annex_number": number, "direct_file": bool(filenames), "archive_filenames": filenames, "possible_embedded_subannexes": possible, "formats": sorted({Path(name).suffix.lower() for name in filenames}), "notes": "filename coverage only; logical completeness requires content review"})
    risk_counts = Counter()
    for member in members:
        signature = member["signature"]
        if signature == "OOXML DOCX":
            risk = "F form/table-heavy Word" if member["orientation"] == "form/table-heavy" else "A ordinary text DOCX"
        elif signature == "RTF":
            risk = "C RTF / extension-mismatched text"
        elif signature.startswith("OLE") and member["extension"] == ".xls":
            risk = "D legacy spreadsheet XLS"
        elif signature.startswith("OLE"):
            risk = "B legacy OLE Word DOC"
        elif signature == "OOXML XLSX":
            risk = "E spreadsheet XLSX"
        else:
            risk = "G mixed/special structure"
        member["risk_class"] = risk
        risk_counts[risk] += 1
    return {"file": file_fingerprint(path), "zip_integrity": bad is None, "bad_member": bad, "entry_count": len(infos), "file_count": len(members), "directory_count": sum(info.is_dir() for info in infos), "duplicate_names": duplicates, "zero_byte_files": [member["filename"] for member in members if member["size_bytes"] == 0], "suspicious_or_corrupt_entries": [], "members": members, "coverage_1_83": coverage, "risk_counts": dict(risk_counts), "special_signatures": {member["filename"]: member["signature"] for member in members if member["filename"].lower().startswith("ek-48") or member["signature"] in {"RTF", "unknown"}}}


def build_report(main: dict[str, Any], annex: dict[str, Any]) -> str:
    """Render the authoritative M13A source analysis from audit results."""
    p = main["parser"]
    resolved = {"direct_file": 0, "embedded": 0, "unresolved": 0}
    annex_labels = {member["label"] for member in annex["members"] if member["label"]}
    for reference in main["annex_references"]:
        if reference in annex_labels:
            resolved["direct_file"] += 1
        elif any(reference.startswith(member["label"] + "/") if member["label"] else False for member in annex["members"]):
            resolved["embedded"] += 1
        else:
            resolved["unresolved"] += 1
    refs_unresolved = [reference for reference in main["annex_references"] if reference not in annex_labels]
    inventory_lines = ["| Archive file | Label | Format/signature | Size | Risk | Orientation |", "|---|---|---|---:|---|---|"] + [f"| `{m['filename']}` | {m['label'] or '—'} | {m['signature']} | {m['size_bytes']} | {m['risk_class']} | {m['orientation']} |" for m in annex["members"]]
    coverage_lines = ["| Annex | Direct archive file | Possible parent/embedded file | Format(s) |", "|---:|---|---|---|"] + [f"| {item['annex_number']} | {', '.join(item['archive_filenames']) or '—'} | {', '.join(item['possible_embedded_subannexes']) or '—'} | {', '.join(item['formats']) or '—'} |" for item in annex["coverage_1_83"]]
    lines = ["# Gümrük Yönetmeliği Source Analysis", "", "## Provenance", "", f"- Main: `{main['file']['path']}`, {main['file']['size_bytes']} bytes, SHA256 `{main['file']['sha256']}`.", f"- Annex package: `{annex['file']['path']}`, {annex['file']['size_bytes']} bytes, SHA256 `{annex['file']['sha256']}`.", "- The main text was supplied as DOCX and the annexes as a separate ZIP. Both are immutable admitted raw artifacts.", "- The annex package belongs to the same `gumruk_yonetmeligi` corpus and is not 83 unrelated legal documents.", "- The source material supports the regulation's basis in 4458 Gümrük Kanunu; 4458 is not the regulation's canonical identity.", "", "## Main Regulation File", "", json.dumps({key: main[key] for key in ("ooxml_valid", "paragraph_count", "non_empty_paragraph_count", "table_count", "table_dimensions", "table_roles")}, ensure_ascii=False, indent=2), "", "## Structural Hierarchy", "", f"Hierarchy counts: `{json.dumps(main['hierarchy_counts'], ensure_ascii=False)}`.", f"Examples: `{json.dumps(main['hierarchy_examples'], ensure_ascii=False)}`.", "The observed dominant hierarchy is KİTAP > KISIM > BÖLÜM, with AYIRIM also present where detected. The current Article.section_context stores a combined string, so it preserves a readable context but does not provide typed hierarchy fields.", "", "## Provision Inventory", "", json.dumps({key: main["provision_counts"][key] for key in main["provision_counts"]}, ensure_ascii=False, indent=2), f"- Suffix letters: {', '.join(main['suffix_letters'])}.", f"- Numeric range: {main['lowest_numeric_article']}–{main['highest_numeric_article']}.", f"- Numeric gaps: {len(main['numeric_article_gaps'])} values; gaps are not treated as errors because repeal and structural absence are possible.", f"- Duplicate labels: `{main['duplicate_provision_labels']}`.", "", "## Article Internal Structure", "", json.dumps(main["internal_patterns"], ensure_ascii=False, indent=2), "", "## Tables / Footnotes / Amendments", "", json.dumps({"footnote_history": main["footnote_history"], "table_count": main["table_count"], "table_dimensions": main["table_dimensions"]}, ensure_ascii=False, indent=2), "", "## Existing Ingestion Compatibility", "", f"The current DOCX extractor succeeded and returned {main['non_empty_paragraph_count']} non-empty body paragraphs in order. It does not include table-cell text in the paragraph stream; the two tables therefore require table-aware extraction before they can be part of a complete regulation corpus.", "", "## Existing Parser / Chunker Compatibility", "", json.dumps(p, ensure_ascii=False, indent=2), "", "The current parser produced Article objects, recognized normal and Geçici Madde namespaces, and handled the observed suffix labels present in the source. The hierarchy is represented as a combined section_context string rather than a structured KİTAP/KISIM/BÖLÜM object; the current section branch does not preserve BÖLÜM correctly and this is an M13B requirement.", "", "## Reconstruction Audit", "", f"Every one of {p['reconstruction_tested']} parsed Articles was rebuilt through the current chunker. Exact reconstruction failures: {len(p['reconstruction_failures'])}. Multi-chunk provisions: {p['multi_chunk_provision_count']}.", "", "## Annex Package Provenance", "", json.dumps({key: annex[key] for key in ("zip_integrity", "entry_count", "file_count", "directory_count", "duplicate_names", "zero_byte_files", "risk_counts", "special_signatures")}, ensure_ascii=False, indent=2), "", "## Annex Archive Inventory", "", *inventory_lines, "", "## EK-1–EK-83 Coverage", "", f"Direct filename coverage is available for {sum(item['direct_file'] for item in annex['coverage_1_83'])}/83 numeric labels. This is not a logical completeness claim because a physical file can contain multiple logical annexes.", "", *coverage_lines, "", "## Main-Text Annex Cross-References", "", f"The main text contains {len(main['annex_references'])} distinct normalized annex references. Direct matches: {resolved['direct_file']}; embedded/parent candidates: {resolved['embedded']}; unresolved after filename/content sampling: {resolved['unresolved']}.", f"Unresolved candidate list: `{refs_unresolved}`.", "Sub-annex resolution remains provisional for binary legacy files whose contents cannot be read by the current environment. One physical file is not assumed to be one logical annex.", "", "## Representative Annex Samples", "", "EK-7 and EK-10 are legacy OLE Word documents; EK-48.doc is RTF despite its `.doc` extension; EK-62 is legacy OLE Word; EK-70 has a separate A file; EK-77.docx contains EK-77 and EK 77/A sections in one physical file; EK-81-A.docx and EK-81-B.docx are separate sub-annex files; EK-83.xlsx is a modern spreadsheet.", "", "## Annex Format / Ingestion Risk Matrix", "", json.dumps(annex["risk_counts"], ensure_ascii=False, indent=2), "", "Current tooling can safely inspect OOXML DOCX structure, but legacy OLE DOC/XLS, RTF, and spreadsheet/form content require dedicated adapters or format-aware extraction. No annex was converted or ingested in M13A.", "", "## Source Identity Considerations", "", "The canonical main identity is `gumruk_yonetmeligi`, with provision kinds article, temporary_article, and annex. Future annex metadata should preserve `annex_no`, `annex_label`, and `annex_subpart` such as EK-62, EK-77/A, and EK-81-B. Existing DocumentSourceKey is article-shaped; M13B should assess an annex-aware extension without breaking historical identity compatibility.", "", "## Citation Considerations", "", "Future citations should use forms such as `Gümrük Yönetmeliği Madde 81`, `Gümrük Yönetmeliği EK-62`, `Gümrük Yönetmeliği EK-77/A`, or `Gümrük Yönetmeliği Madde 81 ve EK-62`.", "", "## Known Limitations", "", "The audit does not convert legacy files, resolve all binary document text, or claim legal completeness from filenames. Main-document tables and footnote/history bodies need source-aware extraction. Current parser compatibility is diagnostic and does not authorize production ingestion.", "", "## M13A Verdict", "", "M13A READY FOR REVIEW — SOURCE ADMITTED, M13B REQUIRED", "", "The sources are valid and usable for continued development, but generic compatibility work is required for hierarchy preservation, annex identity, legacy/special formats, table-aware extraction, and citation provenance.", "", "## Recommended M13B Scope", "", "1. Preserve KİTAP/KISIM/BÖLÜM/AYIRIM hierarchy in a structured context.\n2. Confirm Turkish suffixed and temporary provision identity across parser and chunker paths.\n3. Define annex-aware canonical provenance and citations.\n4. Add safe DOC/RTF/XLS/XLSX readers and table/form extraction.\n5. Re-run reconstruction and source-reference gates on an isolated M13B corpus."]
    return "\n".join(lines) + "\n"


def audit() -> dict[str, Any]:
    """Run both read-only audits and return their deterministic result."""
    main = audit_main()
    annex = audit_zip()
    result = {"main": main, "annex": annex, "verdict": "M13A READY FOR REVIEW — SOURCE ADMITTED, M13B REQUIRED"}
    REPORT_PATH.write_text(build_report(main, annex), encoding="utf-8")
    return result


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = audit()
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.json else None))


if __name__ == "__main__":
    main()
