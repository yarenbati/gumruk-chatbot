"""Source-aware, offline ingestion primitives for regulation annex archives.

The module deliberately stops at structured logical-annex data. It has no
embedding, indexing, retrieval, generation, or Chroma integration.
"""
from __future__ import annotations

import hashlib
import io
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree as ET

from docx import Document
from docx.document import Document as DocumentObject
from docx.table import Table, _Cell
from docx.text.paragraph import Paragraph
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P

from .source_identity import AnnexSourceKey, SourceIdentityError

OOXML = b"PK\x03\x04"
OLE = bytes.fromhex("d0cf11e0a1b11ae1")
RTF = b"{\\rtf"
_LABEL = re.compile(r"\bEK\s*[-–—]?\s*(\d{1,3})(?:(?:\s*[/–—-]\s*|\s+)([A-Za-zÇĞİÖŞÜçğıöşü]))?\b", re.I)
_HEADING = re.compile(r"^\s*[\(\"“]?\s*EK\s*[-–—]?\s*\d{1,3}(?:\s*[/–—-]\s*[A-Za-zÇĞİÖŞÜçğıöşü])?\s*[\"”]?\s*$", re.I)


@dataclass(frozen=True)
class AnnexSourceFile:
    """Immutable physical archive-member provenance."""

    document_id: str
    source_zip_path: str
    source_zip_sha256: str
    archive_member_path: str
    archive_member_filename: str
    archive_member_sha256: str
    detected_file_type: str
    declared_extension: str


@dataclass(frozen=True)
class AnnexBlock:
    """An ordered paragraph, table, spreadsheet, or diagnostic block."""

    kind: str
    source_order: int
    text: str | None = None
    rows: tuple[tuple[str, ...], ...] = ()
    sheet_name: str | None = None
    cells: tuple[tuple[str, Any], ...] = ()
    coordinates: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def render(self) -> str:
        """Render this block deterministically while retaining its structure."""
        if self.kind == "paragraph":
            return self.text or ""
        if self.kind == "table":
            return "\n".join("TABLE | " + " | ".join(cell for cell in row) for row in self.rows)
        if self.kind == "spreadsheet":
            values = "\n".join(f"{coord}={value}" for coord, value in self.cells)
            return f"SHEET | {self.sheet_name}\n{values}"
        return self.text or ""


@dataclass(frozen=True)
class AnnexUnit:
    """Logical annex with ordered structured blocks and physical provenance."""

    source_key: AnnexSourceKey
    human_label: str
    source_member: AnnexSourceFile
    blocks: tuple[AnnexBlock, ...]
    rendered_text: str
    warnings: tuple[str, ...] = ()

    @property
    def storage_id(self) -> str:
        """Return the future stable storage identifier."""
        return self.source_key.storage_id

    def to_dict(self) -> dict[str, Any]:
        """Serialize the unit for deterministic diagnostics or later preparation."""
        return {"source_key": str(self.source_key), "human_label": self.human_label,
                "storage_id": self.storage_id, "source_member": self.source_member.__dict__,
                "blocks": [b.__dict__ for b in self.blocks], "rendered_text": self.rendered_text,
                "warnings": list(self.warnings)}


def sha256_bytes(data: bytes) -> str:
    """Return a SHA256 digest for source provenance."""
    return hashlib.sha256(data).hexdigest()


def detect_file_type(data: bytes) -> str:
    """Detect common member types from content signatures and OOXML parts."""
    if data.startswith(RTF):
        return "RTF"
    if data.startswith(OLE):
        return "OLE_COMPOUND_FILE"
    if data.startswith(OOXML):
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as package:
                names = set(package.namelist())
            if "word/document.xml" in names:
                return "OOXML_DOCX"
            if "xl/workbook.xml" in names:
                return "OOXML_XLSX"
        except zipfile.BadZipFile:
            return "UNKNOWN"
    return "UNKNOWN"


def _filename_key(filename: str, document_id: str) -> AnnexSourceKey | None:
    match = _LABEL.search(Path(filename).stem)
    if not match:
        return None
    return AnnexSourceKey(document_id, int(match.group(1)), match.group(2).upper() if match.group(2) else None)


def _heading_key(text: str, document_id: str) -> AnnexSourceKey | None:
    stripped = text.strip()
    if not _HEADING.match(stripped):
        # Legal amendment annotations commonly precede a genuine heading,
        # e.g. ``(Değişik:RG-...) EK 77/A``. A short annotation-bearing line
        # is still a heading; an ordinary sentence mentioning EK-80 is not.
        if len(stripped) > 120 or "RG-" not in stripped.upper():
            return None
    match = _LABEL.search(text)
    return None if not match else AnnexSourceKey(document_id, int(match.group(1)), match.group(2).upper() if match.group(2) else None)


def _iter_docx_blocks(document: DocumentObject) -> Iterable[Paragraph | Table]:
    """Yield DOCX body paragraphs and tables in their original XML order."""
    parent = document.element.body
    for child in parent.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, document)
        elif isinstance(child, CT_Tbl):
            yield Table(child, document)


def _docx_blocks(data: bytes, document_id: str) -> list[AnnexBlock]:
    document = Document(io.BytesIO(data))
    blocks: list[AnnexBlock] = []
    for order, item in enumerate(_iter_docx_blocks(document)):
        if isinstance(item, Paragraph):
            blocks.append(AnnexBlock("paragraph", order, text=item.text))
        else:
            rows = tuple(tuple(cell.text for cell in row.cells) for row in item.rows)
            blocks.append(AnnexBlock("table", order, rows=rows, metadata={"table_index": sum(b.kind == "table" for b in blocks)}))
    return blocks


def _xml_local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _xlsx_blocks(data: bytes) -> list[AnnexBlock]:
    """Read XLSX with the standard library, preserving sheets and coordinates."""
    blocks: list[AnnexBlock] = []
    with zipfile.ZipFile(io.BytesIO(data)) as package:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in package.namelist():
            root = ET.fromstring(package.read("xl/sharedStrings.xml"))
            for si in root:
                shared.append("".join(t.text or "" for t in si.iter() if _xml_local(t.tag) == "t"))
        workbook = ET.fromstring(package.read("xl/workbook.xml"))
        rels = ET.fromstring(package.read("xl/_rels/workbook.xml.rels"))
        relmap = {r.attrib["Id"]: r.attrib["Target"] for r in rels}
        for sheet in [e for e in workbook.iter() if _xml_local(e.tag) == "sheet"]:
            target = relmap[sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]]
            path = "xl/" + target.lstrip("/") if not target.startswith("xl/") else target
            root = ET.fromstring(package.read(path))
            cells: list[tuple[str, Any]] = []
            for cell in [e for e in root.iter() if _xml_local(e.tag) == "c"]:
                coord = cell.attrib.get("r", "")
                formula = next((x.text for x in cell if _xml_local(x.tag) == "f"), None)
                value = next((x.text for x in cell if _xml_local(x.tag) == "v"), None)
                if value is None and cell.attrib.get("t") == "inlineStr":
                    value = "".join(x.text or "" for x in cell.iter() if _xml_local(x.tag) == "t")
                if value is None and formula is None:
                    continue
                if cell.attrib.get("t") == "s" and value is not None:
                    value = shared[int(value)]
                cells.append((coord, {"value": value, "formula": formula, "cached_value": value if formula else None} if formula else value))
            blocks.append(AnnexBlock("spreadsheet", len(blocks), sheet_name=sheet.attrib.get("name"), cells=tuple(cells), coordinates=tuple(x[0] for x in cells)))
    return blocks


def _rtf_text(data: bytes) -> str:
    """Decode RTF controls, Unicode escapes, tables, and paragraph boundaries."""
    raw = data.decode("cp1252", errors="replace")
    out: list[str] = []
    stack: list[tuple[bool, int]] = []
    skip = False
    uc = 1
    i = 0
    while i < len(raw):
        char = raw[i]
        if char == "{":
            stack.append((skip, uc)); i += 1; continue
        if char == "}":
            if stack: skip, uc = stack.pop()
            i += 1; continue
        if char != "\\":
            if not skip: out.append(char)
            i += 1; continue
        i += 1
        if i >= len(raw): break
        if raw[i] in "\\{}":
            if not skip: out.append(raw[i])
            i += 1; continue
        if raw[i] == "'" and i + 2 < len(raw):
            try:
                if not skip: out.append(bytes.fromhex(raw[i + 1:i + 3]).decode("cp1252"))
            except ValueError: pass
            i += 3; continue
        match = re.match(r"([a-zA-Z]+)(-?\d+)? ?", raw[i:])
        if not match:
            i += 1; continue
        word, number = match.group(1).lower(), match.group(2)
        i += match.end()
        if word in {"fonttbl", "colortbl", "stylesheet", "info", "pict", "object", "header", "footer"}:
            skip = True
        elif word == "uc" and number:
            uc = max(0, int(number))
        elif word == "u" and number:
            value = int(number); value = value if value >= 0 else value + 65536
            if not skip: out.append(chr(value))
            i += uc * (1 if i < len(raw) and raw[i] != "\\" else 0)
        elif word in {"par", "line"} and not skip: out.append("\n")
        elif word == "tab" and not skip: out.append("\t")
    return "".join(out).replace("\r", "")


def _read_member(data: bytes, filename: str) -> tuple[str, list[AnnexBlock], list[str]]:
    detected = detect_file_type(data)
    ext = Path(filename).suffix.lower()
    if detected == "OOXML_DOCX":
        return "docx", _docx_blocks(data, "gumruk_yonetmeligi"), []
    if detected == "OOXML_XLSX":
        return "xlsx", _xlsx_blocks(data), []
    if detected == "RTF":
        text = _rtf_text(data)
        return "rtf", [AnnexBlock("paragraph", 0, text=text)], []
    if detected == "OLE_COMPOUND_FILE" and ext == ".xls":
        return "legacy_xls", [], ["LEGACY_XLS_READER_UNAVAILABLE"]
    if detected == "OLE_COMPOUND_FILE":
        return "legacy_doc", [], ["LEGACY_DOC_READER_UNAVAILABLE"]
    return "unknown", [], ["IMAGE_ONLY_OR_UNEXTRACTED"]


def ingest_member(data: bytes, filename: str, *, source: AnnexSourceFile, document_id: str = "gumruk_yonetmeligi") -> list[AnnexUnit]:
    """Extract one physical member into one or more logical annex units."""
    default = _filename_key(filename, document_id)
    if default is None:
        raise SourceIdentityError(f"cannot derive annex identity from {filename!r}")
    reader, blocks, warnings = _read_member(data, filename)
    segments: list[tuple[AnnexSourceKey, list[AnnexBlock]]] = [(default, [])]
    for block in blocks:
        key = _heading_key(block.text or "", document_id) if block.kind == "paragraph" else None
        if key and key != segments[-1][0]:
            segments.append((key, []))
        segments[-1][1].append(block)
    units: list[AnnexUnit] = []
    for key, segment in segments:
        rendered = "\n".join(block.render() for block in segment if block.render() != "")
        units.append(AnnexUnit(key, key.label, source, tuple(segment), rendered, tuple(warnings)))
    return units


def ingest_archive(zip_path: Path, *, document_id: str = "gumruk_yonetmeligi") -> tuple[list[AnnexUnit], dict[str, Any]]:
    """Read an immutable annex ZIP and return units plus audit diagnostics."""
    zip_bytes = zip_path.read_bytes()
    zip_hash = sha256_bytes(zip_bytes)
    units: list[AnnexUnit] = []
    reader_counts: dict[str, int] = {}
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            data = archive.read(info)
            detected = detect_file_type(data)
            source = AnnexSourceFile(document_id, str(zip_path), zip_hash, info.filename, Path(info.filename).name, sha256_bytes(data), detected, Path(info.filename).suffix.lower())
            member_units = ingest_member(data, info.filename, source=source, document_id=document_id)
            units.extend(member_units)
            reader = "legacy_doc" if detected == "OLE_COMPOUND_FILE" and source.declared_extension != ".xls" else ("legacy_xls" if detected == "OLE_COMPOUND_FILE" else detected.lower())
            reader_counts[reader] = reader_counts.get(reader, 0) + 1
    by_key: dict[AnnexSourceKey, list[AnnexUnit]] = {}
    for unit in units: by_key.setdefault(unit.source_key, []).append(unit)
    duplicate_keys = {str(k): len(v) for k, v in by_key.items() if len(v) > 1}
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as count_archive:
        physical_count = len([i for i in count_archive.infolist() if not i.is_dir()])
    storage_map: dict[str, set[AnnexSourceKey]] = {}
    for key in by_key:
        storage_map.setdefault(key.storage_id, set()).add(key)
    diagnostics = {"physical_member_count": physical_count,
                   "logical_unit_count": len(units), "reader_counts": reader_counts,
                   "extraction_failures": sum(bool(u.warnings) for u in units), "logical_identity_collisions": duplicate_keys,
                   "storage_id_collisions": {storage_id: len(keys) for storage_id, keys in storage_map.items() if len(keys) > 1},
                   "provenance_complete": all(u.source_member.archive_member_sha256 and u.source_member.source_zip_sha256 for u in units),
                   "image_only_or_unextractable_count": sum("IMAGE_ONLY_OR_UNEXTRACTED" in u.warnings for u in units)}
    return units, diagnostics
