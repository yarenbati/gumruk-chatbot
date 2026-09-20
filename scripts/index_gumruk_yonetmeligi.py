"""Explicitly authorized additive indexing with durable API checkpoints."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import struct
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import chromadb
from chromadb.config import Settings
from chromadb.api.types import validate_metadata
from docx import Document
from openai import OpenAI

from scripts import preflight_gumruk_indexing as preflight
from src import config, chunk, ingest
from src.annex_chunk import annex_embedding_input, chunk_annexes
from src.annex_ingest import ingest_archive
from src.embed import build_embedding_text
from src.index import build_chroma_metadata

ROOT = preflight.ROOT
STATE = ROOT / 'data/processed/m13c-b2-indexing'


def canonical(value: Any) -> str:
    """Serialize checkpoints deterministically without non-finite numbers."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def save(path: Path, value: Any) -> None:
    """Atomically persist local recovery state, never secrets."""
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(canonical(value) + '\n', encoding='utf-8')
    temporary.replace(path)


def records() -> list[dict[str, Any]]:
    """Build only the 891 new records using the accepted text/metadata contracts."""
    paragraphs = ingest.extract_paragraphs(Document(str(ROOT / 'data/raw/gumruk-yonetmeligi.docx')))
    main = chunk.build_chunks(chunk.parse_articles(paragraphs, document_id='gumruk_yonetmeligi', legislation_number=None), max_chars=4000)
    units, _ = ingest_archive(ROOT / 'data/raw/gumruk-yonetmeligi-ekler.zip', normalization_manifest=ROOT / 'data/processed/gumruk-yonetmeligi-annex-normalized/normalization-manifest.json')
    annex = chunk_annexes(units, max_chunk_chars=4000)
    result = [{'id': p.chunk_id, 'document': p.text, 'input': build_embedding_text(p), 'metadata': build_chroma_metadata(p)} for p in main]
    result += [{'id': p.chunk_id, 'document': p.text, 'input': annex_embedding_input(p), 'metadata': preflight.annex_chroma_metadata(p)} for p in annex]
    if len(main) != 530 or len(annex) != 361 or len({r['id'] for r in result}) != 891:
        raise ValueError('New record counts/identities changed')
    for record in result:
        validate_metadata(record['metadata'])
        if record['metadata']['document_id'] != 'gumruk_yonetmeligi' or 'legislation_number' in record['metadata']:
            raise ValueError('Noncanonical regulation identity')
    return result


def snapshot(collection: Any) -> dict[str, dict[str, Any]]:
    """Read complete persisted records, including vectors, for exact preservation."""
    payload = collection.get(include=['documents', 'metadatas', 'embeddings'])
    result = {}
    for i, identifier in enumerate(payload['ids']):
        vector = [float(v) for v in payload['embeddings'][i]]
        validate_vectors([vector], 1)
        result[identifier] = {'document': payload['documents'][i], 'metadata': payload['metadatas'][i], 'embedding': vector}
    if len(result) != collection.count():
        raise ValueError('Collection changed during snapshot')
    return result


def validate_vectors(vectors: list[list[float]], expected: int) -> None:
    """Reject missing, non-finite, or non-1536-dimensional vectors."""
    if len(vectors) != expected:
        raise ValueError('Vector count mismatch')
    for vector in vectors:
        if len(vector) != 1536 or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in vector):
            raise ValueError('Invalid vector dimension or value')


def verify_final(current: dict[str, Any], baseline: dict[str, Any], new: list[dict[str, Any]], vectors: list[list[float]]) -> dict[str, int]:
    """Require exact historical records and every canonical new record/vector."""
    if len(baseline) != 375 or len(current) != 1266 or set(baseline).intersection(r['id'] for r in new):
        raise ValueError('Counts or collision gate failed')
    if any(current.get(identifier) != value for identifier, value in baseline.items()):
        raise ValueError('Historical ID/document/metadata/vector changed')
    if set(current) != set(baseline) | {r['id'] for r in new}:
        raise ValueError('Unexpected or missing IDs')
    validate_vectors(vectors, len(new))
    for record, vector in zip(new, vectors):
        stored = current[record['id']]
        if stored['document'] != record['document'] or stored['metadata'] != record['metadata']:
            raise ValueError('New text/metadata/provenance mismatch')
        if struct.pack('<1536f', *stored['embedding']) != struct.pack('<1536f', *vector):
            raise ValueError('Persisted vector mismatch')
    distribution = Counter('gumruk_yonetmeligi' if r['metadata'].get('document_id') == 'gumruk_yonetmeligi' else r['metadata'].get('legislation_number') for r in current.values())
    if distribution != {'5326': 53, '4458': 276, '5607': 46, 'gumruk_yonetmeligi': 891}:
        raise ValueError(f'Unexpected distribution: {distribution}')
    return dict(distribution)


def embed_batch(client: Any, texts: list[str]) -> tuple[list[list[float]], dict[str, int]]:
    """Make one request, mapping validated response indices without retries."""
    response = client.embeddings.create(model='text-embedding-3-small', input=texts, dimensions=1536)
    if response.model != 'text-embedding-3-small' or sorted(item.index for item in response.data) != list(range(len(texts))):
        raise ValueError('API model or index alignment mismatch')
    vectors = [list(item.embedding) for item in sorted(response.data, key=lambda item: item.index)]
    validate_vectors(vectors, len(texts))
    return vectors, {'prompt_tokens': response.usage.prompt_tokens, 'total_tokens': response.usage.total_tokens}


def run() -> dict[str, Any]:
    """Execute or verify one additive run; an already-complete run makes no API calls."""
    if config.EMBEDDING_MODEL != 'text-embedding-3-small':
        raise ValueError('Wrong configured model')
    new = records()
    digest = hashlib.sha256(canonical(new).encode()).hexdigest()
    persisted = preflight.production_ids(ROOT / config.CHROMA_PATH)
    count = len(persisted)
    if count not in {375, 1266}:
        raise ValueError(f'Unexpected/partial collection ({count}); manual review required')
    if count == 375:
        report = preflight.run()
        if not all(report['gates'].values()) or not config.OPENAI_API_KEY or not config.OPENAI_API_KEY.strip():
            raise ValueError('Preflight/API key gate failed')
        STATE.mkdir(parents=True, exist_ok=True)
        backup = STATE / 'production-before'
        if not backup.exists():
            shutil.copytree(ROOT / config.CHROMA_PATH, backup)
        if preflight.production_fingerprints(backup) != report['production_file_sha256']:
            raise ValueError('Backup does not match production baseline')
    elif not (STATE / 'baseline.json').is_file():
        raise ValueError('Missing preservation baseline; cannot certify existing records')

    client = chromadb.PersistentClient(path=str(ROOT / config.CHROMA_PATH), settings=Settings(anonymized_telemetry=False))
    collection = client.get_collection(config.COLLECTION_NAME, embedding_function=None)
    current = snapshot(collection)
    if len(current) != count or client.get_max_batch_size() < len(new):
        raise ValueError('Collection changed or storage batch capacity insufficient; no API calls')
    baseline_path = STATE / 'baseline.json'
    if baseline_path.exists():
        baseline = json.loads(baseline_path.read_text(encoding='utf-8'))
    else:
        if len(current) != 375 or set(current).intersection(r['id'] for r in new):
            raise ValueError('Initial production IDs changed')
        baseline = current
        save(baseline_path, baseline)
    if any(current.get(k) != v for k, v in baseline.items()):
        raise ValueError('Existing production records changed')

    vectors: list[list[float]] = []
    api_calls = 0
    usage = []
    api = None
    for start in range(0, len(new), 64):
        batch = new[start:start + 64]
        path = STATE / f'batch-{start // 64 + 1:03d}.json'
        attempt = path.with_suffix('.attempt.json')
        if path.exists():
            saved = json.loads(path.read_text(encoding='utf-8'))
            if saved['input_digest'] != digest or saved['ids'] != [r['id'] for r in batch]:
                raise ValueError('Checkpoint identity/input mismatch')
        else:
            if count == 1266 or attempt.exists():
                raise ValueError('Missing or ambiguous API checkpoint; no automatic retry')
            if api is None:
                api = OpenAI(api_key=config.OPENAI_API_KEY, max_retries=0, timeout=120)
            save(attempt, {'input_digest': digest, 'ids': [r['id'] for r in batch]})
            batch_vectors, batch_usage = embed_batch(api, [r['input'] for r in batch])
            api_calls += 1
            saved = {'input_digest': digest, 'ids': [r['id'] for r in batch], 'vectors': batch_vectors, 'usage': batch_usage}
            save(path, saved)
            print(f'Embedding batch {start // 64 + 1}/14 completed: {len(batch)} inputs; {batch_usage["total_tokens"]} tokens', flush=True)
        validate_vectors(saved['vectors'], len(batch))
        vectors.extend(saved['vectors'])
        usage.append(saved['usage'])

    if count == 375:
        if snapshot(collection) != baseline:
            raise ValueError('Production changed during embedding; no indexing attempted')
        # add only, never upsert/delete/reset/create. One request avoids deliberate
        # partial batches; API or storage errors propagate without retries.
        if client.get_max_batch_size() < len(new):
            raise ValueError('Storage batch capacity too small; manual review required')
        collection.add(ids=[r['id'] for r in new], documents=[r['document'] for r in new], metadatas=[r['metadata'] for r in new], embeddings=vectors)
    distribution = verify_final(snapshot(collection), baseline, new, vectors)
    result = {'before': 375, 'after': 1266, 'distribution': distribution, 'dimensions': 1536,
              'new_inputs': 891, 'api_calls_this_run': api_calls, 'completed_api_batches': len(usage),
              'api_prompt_tokens': sum(u['prompt_tokens'] for u in usage), 'api_total_tokens': sum(u['total_tokens'] for u in usage),
              'existing_375_exactly_preserved': True, 'all_expected_ids_present': True,
              'canonical_metadata_provenance_valid': True, 'input_digest': digest, 'collisions': 0}
    save(STATE / ('result.json' if count == 375 else 'idempotence.json'), result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true', help='Explicitly authorize paid embedding requests and additive production writes')
    if not parser.parse_args().execute:
        parser.error('--execute is required; no operations performed')
    print(json.dumps(run(), indent=2))
