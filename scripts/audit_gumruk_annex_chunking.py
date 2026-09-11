"""Read-only M13C-A annex chunking and compatibility gates."""
from __future__ import annotations

import contextlib
import io
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import audit_gumruk_annex_ingestion as ingestion
from scripts.audit_gumruk_yonetmeligi_structure import audit_main
from src.annex_chunk import annex_embedding_input, chunk_annexes


def run() -> dict[str, Any]:
    """Verify source compatibility and return actual chunk metrics without writes."""
    with contextlib.redirect_stdout(io.StringIO()):
        source = ingestion.run()
    units, diagnostics = ingestion.ingest_archive(ingestion.ZIP_PATH, normalization_manifest=ingestion.MANIFEST_PATH)
    chunks = chunk_annexes(units, max_chunk_chars=4000)
    reconstructed = sum(''.join(c.text for c in chunks if c.metadata['annex_source_key'] == str(u.source_key)) == u.rendered_text for u in units)
    deterministic = chunks == chunk_annexes(reversed(units), max_chunk_chars=4000)
    main = audit_main()['parser']
    gates = {
        '98_units': len(units) == 98,
        '87_sources': diagnostics['physical_member_count'] == 87,
        '83_base_annexes': source['base_coverage'] == 83,
        '15_sub_annexes': source['sub_annex_count'] == 15,
        '69_references': source['main_reference_total'] == source['main_reference_resolved'] == 69,
        '17_complementary': source['relationship_classification_counts']['COMPLEMENTARY'] == 17 and source['multi_source_logical_annex_count'] == 17,
        '98_reconstruction': reconstructed == 98,
        'no_collisions': len({c.chunk_id for c in chunks}) == len(chunks),
        'deterministic': deterministic,
        'provenance': diagnostics['provenance_complete'] and diagnostics['normalization_provenance_complete'],
        'oversized_explicit': all(c.metadata['oversized_atoms'] for c in chunks if len(c.text) > 4000),
        'main_regulation': main['article_count'] == 528 and main['chunk_count'] == 530 and main['reconstruction_tested'] == 528 and not main['reconstruction_failures'],
    }
    if not all(gates.values()):
        raise ValueError(f'Failed compatibility gates: {gates}')
    representative = {}
    for unit in units:
        if unit.source_key.annex_no not in {10, 33, 83}:
            continue
        pieces = [c for c in chunks if c.metadata['annex_source_key'] == str(unit.source_key)]
        representative[unit.source_key.label] = {
            'chunks': len(pieces), 'characters': len(unit.rendered_text),
            'block_kinds': dict(Counter(b.kind for b in unit.blocks)),
            'source_members': len(unit.source_members or (unit.source_member,)),
            'chunk_lengths': [len(c.text) for c in pieces],
        }
    return {
        'gates': gates, 'annex_units': len(units), 'annex_chunks': len(chunks),
        'reconstruction_pass': reconstructed, 'chunk_id_collisions': len(chunks) - len({c.chunk_id for c in chunks}),
        'soft_target_chars': 4000, 'oversized_chunks': sum(len(c.text) > 4000 for c in chunks),
        'maximum_chunk_chars': max(len(c.text) for c in chunks),
        'oversized_inventory': [
            {'chunk_id': c.chunk_id, 'characters': len(c.text), 'atoms': c.metadata['oversized_atoms']}
            for c in chunks if len(c.text) > 4000
        ],
        'embedding_contract_example': annex_embedding_input(chunks[0]).split('\n\n', 1)[0] + '\n\n<exact chunk text>',
        'representative': representative,
    }


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(run(), ensure_ascii=False, indent=2, sort_keys=True))
