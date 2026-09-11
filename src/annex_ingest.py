"""Source-aware, offline ingestion primitives for regulation annex archives.

The module deliberately stops at structured logical-annex data. It has no
embedding, indexing, retrieval, generation, or Chroma integration.
"""
from __future__ import annotations

import hashlib
import io
import re
import zipfile
from dataclasses import replace
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
    normalization: "NormalizationProvenance | None" = None


@dataclass(frozen=True)
class NormalizationProvenance:
    """Traceable transformation metadata for a legacy Office member."""

    normalization_tool: str
    normalization_tool_version: str
    normalization_command_family: str
    normalized_relative_path: str
    normalized_sha256: str


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
    source_members: tuple[AnnexSourceFile, ...] = ()
    canonical_source_member: AnnexSourceFile | None = None
    multi_source_relationship: str | None = None

    @property
    def storage_id(self) -> str:
        """Return the future stable storage identifier."""
        return self.source_key.storage_id

    def to_dict(self) -> dict[str, Any]:
        """Serialize the unit for deterministic diagnostics or later preparation."""
        return {"source_key": str(self.source_key), "human_label": self.human_label,
                "storage_id": self.storage_id, "source_member": {**{k: v for k, v in self.source_member.__dict__.items() if k != "normalization"}, "normalization": self.source_member.normalization.__dict__ if self.source_member.normalization else None},
                "source_members": [{**{k: v for k, v in member.__dict__.items() if k != "normalization"}, "normalization": member.normalization.__dict__ if member.normalization else None} for member in self.source_members],
                "canonical_source_member": self.canonical_source_member.archive_member_path if self.canonical_source_member else self.source_member.archive_member_path,
                "multi_source_relationship": self.multi_source_relationship,
                "blocks": [b.__dict__ for b in self.blocks], "rendered_text": self.rendered_text,
                "warnings": list(self.warnings)}


def sha256_bytes(data: bytes) -> str:
    """Return a SHA256 digest for source provenance."""
    return hashlib.sha256(data).hexdigest()


def conservative_whitespace_hash(text: str) -> str:
    """Hash text after collapsing whitespace only; legal characters remain unchanged."""
    return sha256_bytes(re.sub(r"\s+", " ", text).strip().encode("utf-8"))


def classify_contributors(units: list[AnnexUnit]) -> str:
    """Classify multi-source content using deterministic text/structure evidence."""
    if len(units) < 2:
        return "UNKNOWN"
    exact = {sha256_bytes(unit.rendered_text.encode("utf-8")) for unit in units}
    if len(exact) == 1:
        return "EXACT_DUPLICATE"
    whitespace = {conservative_whitespace_hash(unit.rendered_text) for unit in units}
    if len(whitespace) == 1:
        return "WHITESPACE_EQUIVALENT"
    texts = [unit.rendered_text.casefold() for unit in units]
    if all(text and any(text in other or other in text for other in texts if other != text) for text in texts):
        return "STRUCTURALLY_EQUIVALENT"
    version_markers = ("version", "eski metin", "yeni metin", "yürürlük tarihi", "değişik")
    if sum(any(marker in text for marker in version_markers) for text in texts) >= 2 and not any("mülga" in text for text in texts):
        return "CONFLICTING"
    if all(texts):
        return "COMPLEMENTARY"
    return "UNKNOWN"


def _dedicated_for_key(unit: AnnexUnit) -> bool:
    """Prefer a filename-derived dedicated member over an embedded section."""
    return _filename_key(unit.source_member.archive_member_filename, unit.source_member.document_id) == unit.source_key


def _canonical_contributor(units: list[AnnexUnit]) -> AnnexUnit:
    return sorted(units, key=lambda unit: (not _dedicated_for_key(unit), unit.source_member.detected_file_type not in {"OOXML_DOCX", "OOXML_XLSX"}, unit.source_member.archive_member_path))[0]


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


def ingest_archive(zip_path: Path, *, document_id: str = "gumruk_yonetmeligi", normalization_manifest: Path | None = None) -> tuple[list[AnnexUnit], dict[str, Any]]:
    """Read an immutable annex ZIP, optionally using approved derived files."""
    zip_bytes = zip_path.read_bytes()
    zip_hash = sha256_bytes(zip_bytes)
    manifest_entries: dict[str, dict[str, Any]] = {}
    manifest_root = normalization_manifest.parent if normalization_manifest else None
    if normalization_manifest and normalization_manifest.exists():
        import json
        manifest_entries = {entry["archive_member_path"]: entry for entry in json.loads(normalization_manifest.read_text(encoding="utf-8"))["entries"]}
    units: list[AnnexUnit] = []
    reader_counts: dict[str, int] = {}
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            data = archive.read(info)
            detected = detect_file_type(data)
            original_hash = sha256_bytes(data)
            entry = manifest_entries.get(info.filename)
            normalized = None
            ingest_data = data
            if entry and entry.get("conversion_status") == "SUCCESS" and manifest_root:
                normalized = NormalizationProvenance(entry["normalization_tool"], entry["normalization_tool_version"], entry["normalization_command_family"], entry["normalized_relative_path"], entry["normalized_sha256"])
                ingest_data = (manifest_root / entry["normalized_relative_path"]).read_bytes()
            source = AnnexSourceFile(document_id, str(zip_path), zip_hash, info.filename, Path(info.filename).name, original_hash, detected, Path(info.filename).suffix.lower(), normalized)
            member_units = ingest_member(ingest_data, info.filename, source=source, document_id=document_id)
            units.extend(member_units)
            if normalized:
                reader = "normalized_docx" if normalized.normalized_relative_path.lower().endswith(".docx") else "normalized_xlsx"
            else:
                reader = "legacy_doc" if detected == "OLE_COMPOUND_FILE" and source.declared_extension != ".xls" else ("legacy_xls" if detected == "OLE_COMPOUND_FILE" else detected.lower())
            reader_counts[reader] = reader_counts.get(reader, 0) + 1
    by_key: dict[AnnexSourceKey, list[AnnexUnit]] = {}
    for unit in units: by_key.setdefault(unit.source_key, []).append(unit)
    relationships = {str(k): [u.source_member.archive_member_path for u in values] for k, values in by_key.items() if len(values) > 1}
    logical_units: list[AnnexUnit] = []
    for key, values in by_key.items():
        first = values[0]
        if len(values) == 1:
            logical_units.append(first)
            continue
        relationship = classify_contributors(values)
        canonical = _canonical_contributor(values)
        if relationship in {"EXACT_DUPLICATE", "WHITESPACE_EQUIVALENT", "STRUCTURALLY_EQUIVALENT"}:
            blocks = tuple(replace(block, metadata={**block.metadata, "archive_member_path": canonical.source_member.archive_member_path}) for block in canonical.blocks)
            rendered = canonical.rendered_text
        elif relationship == "COMPLEMENTARY":
            blocks = tuple(replace(block, metadata={**block.metadata, "archive_member_path": unit.source_member.archive_member_path}) for unit in values for block in unit.blocks)
            rendered = "\n".join(f"SOURCE_MEMBER | {unit.source_member.archive_member_path}\n{unit.rendered_text}" for unit in values if unit.rendered_text)
        else:
            blocks = tuple(replace(block, metadata={**block.metadata, "archive_member_path": unit.source_member.archive_member_path}) for unit in values for block in unit.blocks)
            rendered = "\n".join(f"SOURCE_MEMBER | {unit.source_member.archive_member_path}\n{unit.rendered_text}" for unit in values if unit.rendered_text)
        warnings = tuple(dict.fromkeys(warning for unit in values for warning in unit.warnings))
        logical_units.append(AnnexUnit(key, canonical.human_label, canonical.source_member, blocks, rendered, warnings, tuple(unit.source_member for unit in values), canonical.source_member, relationship))
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as count_archive:
        physical_count = len([i for i in count_archive.infolist() if not i.is_dir()])
    storage_map: dict[str, set[AnnexSourceKey]] = {}
    by_key = {unit.source_key: [unit] for unit in logical_units}
    for key in by_key:
        storage_map.setdefault(key.storage_id, set()).add(key)
    diagnostics = {"physical_member_count": physical_count,
                   "logical_unit_count": len(logical_units), "reader_counts": reader_counts,
                   "extraction_failures": sum(bool(u.warnings) for u in logical_units), "logical_identity_collisions": {},
                   "multi_source_logical_annexes": relationships,
                   "storage_id_collisions": {storage_id: len(keys) for storage_id, keys in storage_map.items() if len(keys) > 1},
                   "provenance_complete": all(member.archive_member_sha256 and member.source_zip_sha256 for u in logical_units for member in (u.source_members or (u.source_member,))),
                   "normalization_provenance_complete": all(member.normalization is not None for u in logical_units for member in (u.source_members or (u.source_member,)) if member.detected_file_type == "OLE_COMPOUND_FILE"),
                   "image_only_or_unextractable_count": sum("IMAGE_ONLY_OR_UNEXTRACTED" in u.warnings for u in logical_units)}
    return logical_units, diagnostics
