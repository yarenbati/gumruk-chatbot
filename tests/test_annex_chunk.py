"""Structure, identity, provenance, and admitted-corpus annex chunk gates."""
from dataclasses import asdict, replace
from pathlib import Path

import pytest

from src.annex_chunk import annex_embedding_input, chunk_annex, chunk_annexes
from src.annex_ingest import AnnexBlock, AnnexSourceFile, AnnexUnit, ingest_archive
from src.source_identity import AnnexSourceKey

ROOT = Path(__file__).resolve().parents[1]


def _unit(blocks: tuple[AnnexBlock, ...]) -> AnnexUnit:
    source = AnnexSourceFile("gumruk_yonetmeligi", "source.zip", "zip-hash", "EK 62.docx", "EK 62.docx", "member-hash", "OOXML_DOCX", ".docx")
    return AnnexUnit(AnnexSourceKey.from_label("EK-62"), "EK-62", source, blocks,
                     "\n".join(block.render() for block in blocks if block.render() != ""))


@pytest.fixture(scope="module")
def corpus() -> list[AnnexUnit]:
    """Read deterministic local ingestion without any external service."""
    units, _ = ingest_archive(ROOT / "data/raw/gumruk-yonetmeligi-ekler.zip", normalization_manifest=ROOT / "data/processed/gumruk-yonetmeligi-annex-normalized/normalization-manifest.json")
    return units


def test_short_annex_and_embedding_contract() -> None:
    unit = _unit((AnnexBlock("paragraph", 0, text=" short\ntext "),))
    chunks = chunk_annex(unit)
    assert len(chunks) == 1
    assert chunks[0].text == unit.rendered_text
    assert chunks[0].chunk_id == "gumruk_yonetmeligi-ek-62-chunk-001"
    assert annex_embedding_input(chunks[0]) == "Gümrük Yönetmeliği\nEK-62\n\n short\ntext "
    assert "legislation_number" not in chunks[0].metadata


def _assert_structure(unit: AnnexUnit, chunks: list) -> None:
    fragments = [b for c in chunks for b in c.blocks]
    position = 0
    for block in unit.blocks:
        parts = []
        if block.kind == 'table' and block.rows:
            while len(parts) < len(block.rows):
                parts.append(fragments[position])
                position += 1
            assert tuple(row for p in parts for row in p.rows) == block.rows
        elif block.kind == 'spreadsheet' and block.cells:
            cells = []
            while len(cells) < len(block.cells):
                part = fragments[position]
                parts.append(part)
                cells.extend(part.cells)
                position += 1
            assert tuple(cells) == block.cells
            assert all(p.sheet_name == block.sheet_name for p in parts)
            assert tuple(coord for p in parts for coord in p.coordinates) == block.coordinates or not block.coordinates
        else:
            parts = [fragments[position]]
            position += 1
            while len(''.join(p.text or '' for p in parts)) < len(block.text or ''):
                parts.append(fragments[position])
                position += 1
            assert ''.join(p.text or '' for p in parts) == (block.text or '')
        for part in parts:
            assert part.source_order == block.source_order
            assert all(part.metadata[k] == v for k, v in block.metadata.items())
    assert position == len(fragments)


def test_large_atomic_blocks_keep_rows_cells_and_sheet_context() -> None:
    blocks = (AnnexBlock("paragraph", 0, text="p" * 4001),
              AnnexBlock("table", 1, rows=(("a\nb", "", "c" * 4500), ("last", "cell", ""))),
              AnnexBlock("spreadsheet", 2, sheet_name="Sheet One", cells=(("A1", "x" * 4100), ("B1", {"formula": "SUM(A1)", "cached_value": "2", "value": "2"}))),
              AnnexBlock("paragraph", 3, text="end"))
    unit = _unit(blocks)
    chunks = chunk_annex(unit, max_chunk_chars=4000)
    _assert_structure(unit, chunks)
    assert "".join(c.text for c in chunks) == unit.rendered_text
    oversized = [c for c in chunks if len(c.text) > 4000]
    assert len(oversized) == 3
    assert all(c.metadata['oversized_atoms'] for c in oversized)
    for chunk in chunks:
        assert unit.rendered_text[chunk.metadata['char_start']:chunk.metadata['char_end']] == chunk.text


def test_soft_target_and_empty_blocks_preserve_separators() -> None:
    unit = _unit(tuple(AnnexBlock("paragraph", i, text=text) for i, text in enumerate(["", "abc", "", "def", ""])))
    chunks = chunk_annex(unit, max_chunk_chars=4)
    assert [c.text for c in chunks] == ["abc", "\ndef"]
    assert tuple(b for c in chunks for b in c.blocks) == unit.blocks
    assert chunk_annex(_unit(()))[0].text == ""


@pytest.mark.parametrize("target", [0, -1, True, 1.5])
def test_invalid_target_rejected(target: int) -> None:
    with pytest.raises(ValueError):
        chunk_annex(_unit(()), max_chunk_chars=target)


def test_mismatched_rendering_and_duplicate_identity_fail_closed() -> None:
    unit = _unit((AnnexBlock("paragraph", 0, text="body"),))
    with pytest.raises(ValueError, match="rendering mismatch"):
        chunk_annex(replace(unit, rendered_text="different"))
    with pytest.raises(ValueError, match="Duplicate annex"):
        chunk_annexes([unit, unit])
    with pytest.raises(ValueError, match="Unresolved"):
        chunk_annex(replace(unit, multi_source_relationship="UNKNOWN"))


def test_corpus_98_reconstructions_unique_deterministic_ids_and_provenance(corpus: list[AnnexUnit]) -> None:
    assert len(corpus) == 98
    assert {u.source_key.annex_no for u in corpus if not u.source_key.annex_subpart} == set(range(1, 84))
    assert sum(u.source_key.annex_subpart is not None for u in corpus) == 15
    chunks = chunk_annexes(corpus, max_chunk_chars=4000)
    assert chunks == chunk_annexes(reversed(corpus), max_chunk_chars=4000)
    assert len({c.chunk_id for c in chunks}) == len(chunks)
    for unit in corpus:
        pieces = [c for c in chunks if c.metadata['annex_source_key'] == str(unit.source_key)]
        assert pieces
        assert "".join(c.text for c in pieces) == unit.rendered_text
        _assert_structure(unit, pieces)
        for index, chunk in enumerate(pieces, 1):
            assert chunk.chunk_id == f"{unit.storage_id}-chunk-{index:03d}"
            assert chunk.metadata['source_members'] == [asdict(m) for m in (unit.source_members or (unit.source_member,))]
            assert chunk.metadata['document_id'] == 'gumruk_yonetmeligi'
            assert chunk.metadata['source_type'] == 'annex'
            assert chunk.metadata['annex_label'] == unit.source_key.label
            assert chunk.metadata['annex_storage_id'] == unit.storage_id
            assert chunk.metadata['annex_no'] == unit.source_key.annex_no
            assert chunk.metadata['annex_subpart'] == unit.source_key.annex_subpart


def test_ek10_subannex_ek33_complementary_and_ek83_spreadsheet(corpus: list[AnnexUnit]) -> None:
    by_label = {u.source_key.label: u for u in corpus}
    subannexes = [u for u in corpus if u.source_key.annex_no == 10 and u.source_key.annex_subpart]
    assert subannexes
    for unit in subannexes:
        assert all(c.metadata['annex_subpart'] == unit.source_key.annex_subpart for c in chunk_annex(unit))
    assert chunk_annex(by_label['EK-77/A'])[0].chunk_id == 'gumruk_yonetmeligi-ek-77-a-chunk-001'
    unit = by_label['EK-33']
    assert unit.multi_source_relationship == 'COMPLEMENTARY'
    chunks = chunk_annex(unit)
    assert sum('SOURCE_MEMBER | ' in c.text for c in chunks) == len(unit.source_members)
    for chunk in chunks:
        assert {b.metadata['archive_member_path'] for b in chunk.blocks} == {chunk.metadata['contributing_source_member']['archive_member_path']}
        assert len(chunk.metadata['source_members']) == len(unit.source_members)
    spreadsheet = by_label['EK-83']
    assert any(b.kind == 'spreadsheet' for b in spreadsheet.blocks)
    _assert_structure(spreadsheet, chunk_annex(spreadsheet))


def test_large_table_splits_only_at_rows_with_empty_and_multiline_cells() -> None:
    rows = tuple((str(i), 'legal\ntext' * 90, '') for i in range(30))
    unit = _unit((AnnexBlock('table', 0, rows=rows, metadata={'table_index': 7}),))
    chunks = chunk_annex(unit, max_chunk_chars=4000)
    assert len(chunks) > 1
    assert max(len(c.text) for c in chunks) <= 4000
    assert ''.join(c.text for c in chunks) == unit.rendered_text
    _assert_structure(unit, chunks)
    assert chunks == chunk_annex(unit, max_chunk_chars=4000)
    assert all(c.metadata['source_members'] == [asdict(unit.source_member)] for c in chunks)


def test_large_spreadsheet_row_groups_and_whole_cell_fallback() -> None:
    cells = tuple((f'{column}{row}', {'value': 'v' * 1400, 'formula': 'A1+1', 'cached_value': '2'})
                  for row in range(1, 8) for column in ('A', 'B', 'C'))
    unit = _unit((AnnexBlock('spreadsheet', 0, sheet_name='Legal sheet', cells=cells,
                            coordinates=tuple(coord for coord, _ in cells)),))
    chunks = chunk_annex(unit, max_chunk_chars=4000)
    assert len(chunks) > 1
    assert max(len(c.text) for c in chunks) <= 4000
    assert ''.join(c.text for c in chunks) == unit.rendered_text
    assert sum(c.text.count('SHEET | Legal sheet') for c in chunks) == 1
    _assert_structure(unit, chunks)
    assert chunks == chunk_annex(unit, max_chunk_chars=4000)
    assert len({c.chunk_id for c in chunks}) == len(chunks)
    assert all(c.metadata['contributing_source_member'] == asdict(unit.source_member) for c in chunks)


def test_oversized_multiline_paragraph_uses_existing_newlines_only() -> None:
    unit = _unit((AnnexBlock('paragraph', 0, text='\n'.join(['legal text ' * 90] * 20)),))
    chunks = chunk_annex(unit, max_chunk_chars=4000)
    assert len(chunks) > 1
    assert max(len(c.text) for c in chunks) <= 4000
    assert ''.join(c.text for c in chunks) == unit.rendered_text
    _assert_structure(unit, chunks)


def test_ids_are_document_scoped() -> None:
    first = _unit(())
    second = replace(first, source_key=AnnexSourceKey('another_document', 62))
    assert len({c.chunk_id for c in chunk_annexes([first, second])}) == 2
