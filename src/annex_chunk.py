"""Offline annex chunking and text-only embedding contract; no model calls."""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import re
from typing import Any, Iterable

from . import config
from .annex_ingest import AnnexBlock, AnnexSourceFile, AnnexUnit


@dataclass(frozen=True)
class AnnexChunk:
    """An exact text slice with structured fragments and source metadata."""

    chunk_id: str
    text: str
    blocks: tuple[AnnexBlock, ...]
    metadata: dict[str, Any]


def _sections(unit: AnnexUnit) -> list[tuple[AnnexSourceFile, tuple[AnnexBlock, ...]]]:
    if unit.multi_source_relationship in {"CONFLICTING", "UNKNOWN"}:
        raise ValueError("Unresolved annex contributors cannot be chunked")
    if unit.multi_source_relationship != "COMPLEMENTARY":
        return [(unit.canonical_source_member or unit.source_member, unit.blocks)]
    members = {m.archive_member_path: m for m in unit.source_members}
    sections: list[tuple[AnnexSourceFile, tuple[AnnexBlock, ...]]] = []
    for block in unit.blocks:
        path = block.metadata.get("archive_member_path")
        if path not in members:
            raise ValueError("Complementary block lacks known source-member provenance")
        member = members[path]
        if sections and sections[-1][0] == member:
            sections[-1] = (member, (*sections[-1][1], block))
        else:
            sections.append((member, (block,)))
    return sections


def _fragments(block: AnnexBlock, target: int) -> list[tuple[str, AnnexBlock]]:
    """Return exact ordered text fragments; ranges are zero-based, end-exclusive."""
    if block.kind == "paragraph" and len(block.render()) > target and "\n" in block.render():
        # Native RTF ingestion can store many explicit lines in one paragraph
        # block. Existing newlines are safe fallback boundaries, never offsets
        # chosen by character count. Ordinary short paragraphs remain whole.
        fragments = []
        offset = 0
        for i, line in enumerate(block.render().split("\n")):
            text = ("\n" if i else "") + line
            fragments.append((text, replace(block, text=text, metadata={**block.metadata,
                "fragment_text_start": offset, "fragment_text_end": offset + len(text)})))
            offset += len(text)
        return fragments
    if block.kind == "table" and block.rows:
        return [(("\n" if i else "") + "TABLE | " + " | ".join(row),
                 replace(block, rows=(row,), metadata={**block.metadata, "fragment_row_start": i, "fragment_row_end": i + 1}))
                for i, row in enumerate(block.rows)]
    if block.kind != "spreadsheet" or not block.cells:
        return [(block.render(), block)]
    groups: list[list[int]] = []
    previous_row = None
    for i, (coordinate, _) in enumerate(block.cells):
        match = re.fullmatch(r"[A-Za-z]+([0-9]+)", coordinate)
        row = match.group(1) if match else None
        if groups and row is not None and row == previous_row:
            groups[-1].append(i)
        else:
            groups.append([i])
        previous_row = row
    fragments = []
    for group in groups:
        # An oversized spreadsheet row can safely fall back to whole cells.
        groups_to_emit = [group]
        header_size = len(f"SHEET | {block.sheet_name}\n") if group[0] == 0 else 0
        if header_size + sum(len(f"{block.cells[i][0]}={block.cells[i][1]}") + 1 for i in group) > target:
            groups_to_emit = [[i] for i in group]
        for indices in groups_to_emit:
            start, end = indices[0], indices[-1] + 1
            cells = block.cells[start:end]
            prefix = f"SHEET | {block.sheet_name}\n" if start == 0 else "\n"
            text = prefix + "\n".join(f"{coord}={value}" for coord, value in cells)
            fragment = replace(block, cells=cells, coordinates=tuple(coord for coord, _ in cells),
                               metadata={**block.metadata, "fragment_cell_start": start, "fragment_cell_end": end,
                                         "sheet_header_in_text": start == 0})
            fragments.append((text, fragment))
    return fragments


def chunk_annex(unit: AnnexUnit, *, max_chunk_chars: int | None = None) -> list[AnnexChunk]:
    """Pack paragraphs, table rows, and spreadsheet row/cell groups exactly.

    Tables split only between rows; sheets split between rows, falling back
    to whole cells for oversized rows. Paragraphs stay intact when practical;
    oversized multiline blocks may split at existing newlines.
    Unavoidable oversized atoms are explicitly reported. Source changes always
    start a new chunk. Separating newlines belong to the following chunk;
    reconstruction is direct concatenation, without trimming or overlap.
    """
    target = config.MAX_CHUNK_CHARS if max_chunk_chars is None else max_chunk_chars
    if isinstance(target, bool) or not isinstance(target, int) or target <= 0:
        raise ValueError("max_chunk_chars must be a positive integer")
    packed: list[tuple[str, tuple[AnnexBlock, ...], AnnexSourceFile]] = []
    has_text = False
    for member, blocks in _sections(unit):
        nonempty = any(block.render() != "" for block in blocks)
        prefix = ""
        if unit.multi_source_relationship == "COMPLEMENTARY" and nonempty:
            prefix = ("\n" if has_text else "") + f"SOURCE_MEMBER | {member.archive_member_path}\n"
        text = prefix
        held: list[AnnexBlock] = []
        section_has_text = False
        for block in blocks:
            rendered = block.render()
            separator = "\n" if rendered and (section_has_text or (has_text and not prefix)) else ""
            for fragment_index, (fragment_text, fragment) in enumerate(_fragments(block, target)):
                atom = (separator if fragment_index == 0 else "") + fragment_text
                # Never leave a SOURCE_MEMBER header in a chunk by itself.
                if text and held and any(b.render() for b in held) and len(text) + len(atom) > target:
                    packed.append((text, tuple(held), member))
                    text, held = "", []
                if len(text) + len(atom) > target:
                    reason = "table_row" if fragment.kind == "table" else ("spreadsheet_cell_or_row" if fragment.kind == "spreadsheet" else "paragraph")
                    fragment = replace(fragment, metadata={**fragment.metadata, "oversized_atomic": {
                        "reason": reason, "atomic_text_chars": len(atom),
                        "boundary_prefix_chars": len(text), "target_chars": target,
                        "source_order": fragment.source_order,
                    }})
                text += atom
                held.append(fragment)
            if rendered:
                section_has_text = True
        if text or held:
            packed.append((text, tuple(held), member))
        has_text = has_text or nonempty
    if not packed:
        packed.append(("", (), unit.source_member))
    if "".join(text for text, _, _ in packed) != unit.rendered_text:
        raise ValueError(f"Structured rendering mismatch for {unit.source_key}")
    key = unit.source_key
    sources = unit.source_members or (unit.source_member,)
    chunks = []
    offset = 0
    for index, (text, blocks, member) in enumerate(packed, 1):
        chunk_id = f"{unit.storage_id}-chunk-{index:03d}"
        metadata = {
            "document_id": key.document_id, "source_type": "annex",
            "annex_no": key.annex_no, "annex_subpart": key.annex_subpart,
            "annex_label": key.label, "annex_source_key": str(key),
            "annex_storage_id": unit.storage_id, "chunk_id": chunk_id,
            "chunk_index": index, "char_start": offset, "char_end": offset + len(text),
            "source_members": [asdict(source) for source in sources],
            "contributing_source_member": asdict(member),
            "canonical_source_member": asdict(unit.canonical_source_member or unit.source_member),
            "multi_source_relationship": unit.multi_source_relationship,
            "warnings": list(unit.warnings),
            "oversized_atoms": [
                {**block.metadata["oversized_atomic"], "kind": block.kind,
                 "row_start": block.metadata.get("fragment_row_start"),
                 "row_end": block.metadata.get("fragment_row_end"),
                 "cell_start": block.metadata.get("fragment_cell_start"),
                 "cell_end": block.metadata.get("fragment_cell_end"),
                 "text_start": block.metadata.get("fragment_text_start"),
                 "text_end": block.metadata.get("fragment_text_end"),
                 "sheet_name": block.sheet_name, "coordinates": list(block.coordinates),
                 "archive_member_path": member.archive_member_path}
                for block in blocks if "oversized_atomic" in block.metadata
            ],
        }
        chunks.append(AnnexChunk(chunk_id, text, blocks, metadata))
        offset += len(text)
    return chunks


def chunk_annexes(units: Iterable[AnnexUnit], *, max_chunk_chars: int | None = None) -> list[AnnexChunk]:
    """Chunk in canonical annex order, rejecting duplicate identities and IDs."""
    ordered = sorted(units, key=lambda unit: unit.source_key)
    if len({unit.source_key for unit in ordered}) != len(ordered):
        raise ValueError("Duplicate annex identities")
    chunks = [chunk for unit in ordered for chunk in chunk_annex(unit, max_chunk_chars=max_chunk_chars)]
    if len({chunk.chunk_id for chunk in chunks}) != len(chunks):
        raise ValueError("Annex chunk ID collision")
    return chunks


def annex_embedding_input(chunk: AnnexChunk, *, document_title: str = "Gümrük Yönetmeliği") -> str:
    """Return title + newline + canonical annex label + blank line + exact text.

    This text-only contract does not invoke or modify existing embedding code.
    Callers preparing other documents must supply their document title.
    """
    return f"{document_title}\n{chunk.metadata['annex_label']}\n\n{chunk.text}"
