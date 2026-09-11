"""Offline M13C-B1 input validation; never creates clients or writes Chroma."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path
from typing import Any
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import tiktoken
import tiktoken.load
from chromadb.api.types import validate_metadata
from docx import Document

from src import config, chunk, ingest
from src.annex_chunk import AnnexChunk, annex_embedding_input, chunk_annexes
from src.annex_ingest import ingest_archive
from src.embed import build_embedding_text
from src.index import build_chroma_metadata

ROOT = Path(__file__).resolve().parents[1]


def annex_chroma_metadata(piece: AnnexChunk) -> dict[str, Any]:
    """Project filterable scalars plus lossless canonical JSON of all provenance.

    This is a proposed annex-only storage adapter, not a production index change.
    Nested domain dictionaries and lists of source dictionaries cannot be sent
    directly as Chroma metadata. Nulls stay in JSON and are omitted as filters.
    """
    metadata = {key: value for key, value in piece.metadata.items()
                if isinstance(value, (str, int, float, bool))}
    metadata['annex_metadata_json'] = json.dumps(piece.metadata, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
    validate_metadata(metadata)
    return metadata


def plan_batches(counts: list[int], *, model: str, batch_size: int = 64) -> list[list[int]]:
    """Fail closed on unsafe inputs/models and pack request indices in order.

    Reviewed API contract: 8192 tokens/input, 300000 tokens/request, at most
    2048 inputs/request. Source: https://developers.openai.com/api/reference/
    ruby/resources/embeddings/methods/create (reviewed 2026-09-11).
    """
    if model != 'text-embedding-3-small':
        raise ValueError(f'Unreviewed embedding model: {model}')
    if not 1 <= batch_size <= 2048:
        raise ValueError('Invalid batch size')
    unsafe = [(index, count) for index, count in enumerate(counts) if count <= 0 or count > 8192]
    if unsafe:
        raise ValueError(f'Unsafe embedding input indices/token counts: {unsafe}')
    batches: list[list[int]] = []
    current: list[int] = []
    total = 0
    for index, count in enumerate(counts):
        if current and (len(current) >= batch_size or total + count > 300000):
            batches.append(current)
            current, total = [], 0
        current.append(index)
        total += count
    if current:
        batches.append(current)
    return batches


def production_fingerprints(path: Path) -> dict[str, str]:
    """Hash all production files without opening a Chroma client."""
    return {str(p.relative_to(path)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(path.rglob('*')) if p.is_file()}


def production_ids(path: Path) -> list[tuple[str, str]]:
    """Read persisted collection identities with an immutable SQLite connection."""
    database = path / 'chroma.sqlite3'
    if not database.is_file() or Path(str(database) + '-wal').exists():
        raise ValueError('Stable checkpointed production database required; no writes attempted')
    connection = sqlite3.connect(database.resolve().as_uri() + '?mode=ro&immutable=1', uri=True)
    try:
        return connection.execute(
            'SELECT e.embedding_id,m.string_value FROM embeddings e '
            'JOIN segments s ON e.segment_id=s.id JOIN collections c ON s.collection=c.id '
            'LEFT JOIN embedding_metadata m ON m.id=e.id AND m.key=? '
            'WHERE c.name=? ORDER BY e.embedding_id',
            ('legislation_number', config.COLLECTION_NAME)).fetchall()
    finally:
        connection.close()


def run() -> dict[str, Any]:
    """Inspect all 891 inputs and return a text-free, read-only preflight report."""
    store = ROOT / config.CHROMA_PATH
    before = production_fingerprints(store)
    existing = production_ids(store)
    paragraphs = ingest.extract_paragraphs(Document(str(ROOT / 'data/raw/gumruk-yonetmeligi.docx')))
    main = chunk.build_chunks(chunk.parse_articles(paragraphs, document_id='gumruk_yonetmeligi', legislation_number=None), max_chars=4000)
    units, _ = ingest_archive(ROOT / 'data/raw/gumruk-yonetmeligi-ekler.zip', normalization_manifest=ROOT / 'data/processed/gumruk-yonetmeligi-annex-normalized/normalization-manifest.json')
    annex = chunk_annexes(units, max_chunk_chars=4000)
    inputs = [(p.chunk_id, build_embedding_text(p), build_chroma_metadata(p)) for p in main]
    inputs += [(p.chunk_id, annex_embedding_input(p), annex_chroma_metadata(p)) for p in annex]
    if config.EMBEDDING_MODEL != 'text-embedding-3-small':
        raise ValueError('Configured model has not been reviewed')
    # read_file is reached only on a tokenizer cache miss; never fetch remotely.
    with patch.object(tiktoken.load, 'read_file', side_effect=RuntimeError('Tokenizer cache missing; offline preflight stopped')):
        encoding = tiktoken.encoding_for_model(config.EMBEDDING_MODEL)
    inventory = [{'chunk_id': identifier, 'characters': len(text),
                  'tokens': len(encoding.encode(text, disallowed_special=())),
                  'input_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest()}
                 for identifier, text, metadata in inputs]
    unsafe = [row for row in inventory if row['tokens'] > 8192 or row['tokens'] <= 0]
    if unsafe:
        raise ValueError('Unsafe inputs; STOP: ' + json.dumps(unsafe))
    counts = [row['tokens'] for row in inventory]
    batches = plan_batches(counts, model=config.EMBEDDING_MODEL)
    ids = [identifier for identifier, _, _ in inputs]
    for _, text, metadata in inputs:
        validate_metadata(metadata)
        json.dumps(metadata, allow_nan=False)
        if metadata['document_id'] != 'gumruk_yonetmeligi' or not text.strip():
            raise ValueError('Wrong document identity or empty input')
    for piece in annex:
        projected = annex_chroma_metadata(piece)
        if json.loads(projected['annex_metadata_json']) != piece.metadata or 'legislation_number' in projected:
            raise ValueError('Annex identity/provenance mismatch')
    repeated = [(p.chunk_id, build_embedding_text(p)) for p in main]
    repeated += [(p.chunk_id, annex_embedding_input(p)) for p in chunk_annexes(reversed(units), max_chunk_chars=4000)]
    gates = {
        'main_530': len(main) == 530, 'annex_361': len(annex) == 361,
        'new_891_unique': len(ids) == len(set(ids)) == 891,
        'production_375': len(existing) == len({i for i, _ in existing}) == 375,
        'production_law_counts': Counter(law for _, law in existing) == {'5326':53, '4458':276, '5607':46},
        'no_existing_collisions': not set(ids).intersection(i for i, _ in existing),
        'deterministic_inputs': repeated == [(i, t) for i, t, _ in inputs],
        'all_inputs_safe': not unsafe,
        'metadata_compatible': True,
        'production_unchanged': before == production_fingerprints(store),
    }
    if not all(gates.values()):
        raise ValueError(f'Failed preflight gates: {gates}')
    ranked = sorted(inventory, key=lambda row: (-row['tokens'], row['chunk_id']))
    return {
        'status': 'M13C-B1 READY — INDEXING PREFLIGHT PASS', 'gates': gates,
        'model': config.EMBEDDING_MODEL, 'encoding': encoding.name,
        'main_chunks': len(main), 'annex_chunks': len(annex), 'new_inputs': len(inputs),
        'production_vectors': len(existing), 'production_law_counts': dict(Counter(law for _, law in existing)),
        'expected_post_index_vectors': len(existing) + len(inputs),
        'total_input_tokens': sum(counts), 'maximum_input_tokens': max(counts),
        'largest_inputs_by_tokens': ranked[:10],
        'unusual_definition': 'input characters > 4000 OR tokens >= 4096; headers included',
        'unusually_large_inputs': [row for row in ranked if row['characters'] > 4000 or row['tokens'] >= 4096],
        'batches': [{'inputs': len(batch), 'tokens': sum(counts[i] for i in batch)} for batch in batches],
        'proposed_batch_count': len(batches),
        'batching_note': 'Sequential requests, <=64 inputs and <=300000 tokens; account rate limits remain runtime constraints.',
        'annex_metadata_contract': 'Filterable scalars plus lossless canonical annex_metadata_json; no production integration yet.',
        'production_file_sha256': before,
    }


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(run(), ensure_ascii=False, indent=2, sort_keys=True))
