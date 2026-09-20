"""Read-only M13D-A source/key audit; no clients, embeddings, or retrieval."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from docx import Document

from src import chunk, config, ingest
from src.annex_chunk import chunk_annexes
from src.annex_ingest import ingest_archive
from src.source_identity import AnnexSourceKey, DocumentSourceKey

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / 'evaluation/questions_gumruk_yonetmeligi.json'
DOCUMENT_ID = 'gumruk_yonetmeligi'


def source_key(metadata: dict[str, Any]) -> str:
    """Validate indexed identity and serialize the appropriate domain key."""
    if metadata.get('document_id') != DOCUMENT_ID or metadata.get('legislation_number'):
        raise ValueError('Noncanonical regulation identity')
    if metadata.get('source_type') == 'annex':
        key = AnnexSourceKey(DOCUMENT_ID, metadata['annex_no'], metadata.get('annex_subpart') or None)
        if metadata.get('annex_source_key') != str(key):
            raise ValueError('Indexed annex key mismatch')
        return str(key)
    return str(DocumentSourceKey(DOCUMENT_ID, metadata['article_type'], metadata['article_no']))


def validate_dataset(dataset: dict[str, Any], texts: dict[str, str]) -> dict[str, Any]:
    """Require 30 canonical questions and literal evidence for every source."""
    if dataset.get('source_identity_schema') != 'document-annex-source-v1':
        raise ValueError('Unexpected identity schema')
    questions = dataset['questions']
    if len(questions) != 30:
        raise ValueError('Expected 30 questions')
    seen: set[str] = set()
    composition: Counter[str] = Counter()
    matched: dict[str, list[str]] = {}
    for index, question in enumerate(questions, 1):
        if question['id'] != f'gy-{index:03d}' or question['document_id'] != DOCUMENT_ID:
            raise ValueError('Question identity mismatch')
        normalized = ' '.join(question['question'].casefold().split())
        if not normalized or normalized in seen:
            raise ValueError('Empty or duplicate question')
        seen.add(normalized)
        if question['difficulty'] not in {'easy', 'medium', 'hard'}:
            raise ValueError('Invalid difficulty')
        if question['source_verified'] is not True or question['expert_validated'] is not False:
            raise ValueError('Invalid review status')
        if not question['notes'].strip() or question['expected_document_ids'] != [DOCUMENT_ID]:
            raise ValueError('Missing evidence note or wrong expected document')
        keys = []
        for source in question['expected_sources']:
            if source.get('source_type') == 'annex':
                key = AnnexSourceKey(source['document_id'], source['annex_no'], source.get('annex_subpart'))
            else:
                key = DocumentSourceKey.from_dict(source)
            if key.document_id != DOCUMENT_ID:
                raise ValueError('Wrong expected document identity')
            keys.append(str(key))
        if not keys or len(set(keys)) != len(keys) or keys != question['expected_source_keys']:
            raise ValueError('Expected key serialization mismatch')
        if set(question['evidence']) != set(keys):
            raise ValueError('Every expected source needs evidence')
        for key in keys:
            if key not in texts:
                raise ValueError(f'Missing indexed source: {key}')
            excerpt = question['evidence'][key]
            if not excerpt.strip() or excerpt not in texts[key]:
                raise ValueError(f'Evidence not found: {question["id"]}: {key}')
        annexes = sum('/annex/' in key for key in keys)
        composition['mixed' if 0 < annexes < len(keys) else 'annex_only' if annexes else 'article_only'] += 1
        composition['multi_source'] += len(keys) > 1
        matched[question['id']] = keys
    return {'questions': len(questions), 'composition': dict(composition),
            'difficulty': dict(Counter(q['difficulty'] for q in questions)),
            'distinct_expected_keys': len({k for keys in matched.values() for k in keys}),
            'validated_expected_keys': matched}


def audit() -> dict[str, Any]:
    """Compare immutable indexed text with admitted sources and audit the freeze."""
    database = ROOT / config.CHROMA_PATH / 'chroma.sqlite3'
    if not database.is_file() or Path(str(database) + '-wal').exists():
        raise ValueError('Stable checkpointed database required')
    before = hashlib.sha256(database.read_bytes()).hexdigest()
    connection = sqlite3.connect(database.resolve().as_uri() + '?mode=ro&immutable=1', uri=True)
    indexed: dict[str, tuple[str, str]] = {}
    distribution: Counter[str] = Counter()
    try:
        rows = connection.execute(
            'SELECT e.id,e.embedding_id FROM embeddings e JOIN segments s ON e.segment_id=s.id '
            'JOIN collections c ON s.collection=c.id WHERE c.name=?', (config.COLLECTION_NAME,)).fetchall()
        for internal, identifier in rows:
            metadata = {key: string if string is not None else integer for key, string, integer in
                        connection.execute('SELECT key,string_value,int_value FROM embedding_metadata WHERE id=?', (internal,))}
            distribution[metadata['document_id']] += 1
            if metadata['document_id'] == DOCUMENT_ID:
                indexed[identifier] = (source_key(metadata), metadata['chroma:document'])
    finally:
        connection.close()
    paragraphs = ingest.extract_paragraphs(Document(str(ROOT / 'data/raw/gumruk-yonetmeligi.docx')))
    main = chunk.build_chunks(chunk.parse_articles(paragraphs, document_id=DOCUMENT_ID, legislation_number=None), max_chars=4000)
    units, _ = ingest_archive(ROOT / 'data/raw/gumruk-yonetmeligi-ekler.zip', normalization_manifest=
                              ROOT / 'data/processed/gumruk-yonetmeligi-annex-normalized/normalization-manifest.json')
    annexes = chunk_annexes(units, max_chunk_chars=4000)
    rebuilt = {p.chunk_id: p.text for p in [*main, *annexes]}
    if rebuilt != {identifier: text for identifier, (_, text) in indexed.items()}:
        raise ValueError('Indexed text differs from admitted-source reconstruction')
    texts: dict[str, str] = {}
    for identifier in sorted(indexed):
        key, text = indexed[identifier]
        texts[key] = texts.get(key, '') + text
    dataset = json.loads(DATASET.read_text(encoding='utf-8'))
    result = validate_dataset(dataset, texts)
    after = hashlib.sha256(database.read_bytes()).hexdigest()
    if before != after:
        raise ValueError('Production database changed during read-only audit')
    return {'baseline': dataset['baseline_commit'], 'dataset_sha256': hashlib.sha256(DATASET.read_text(encoding='utf-8').encode('utf-8')).hexdigest(),
            'collection': config.COLLECTION_NAME, 'collection_total': len(rows), 'distribution': dict(distribution),
            'article_chunks': len(main), 'annex_chunks': len(annexes),
            'article_keys': sum('/annex/' not in key for key in texts),
            'annex_keys': sum('/annex/' in key for key in texts),
            'identity_validation': 'PASS', 'admitted_source_text_match': 'PASS',
            'production_sqlite_sha256': before, 'production_unchanged': True,
            'raw_source_sha256': {name: hashlib.sha256((ROOT / 'data/raw' / name).read_bytes()).hexdigest()
                                  for name in ['gumruk-yonetmeligi.docx', 'gumruk-yonetmeligi-ekler.zip']}, **result}


if __name__ == '__main__':
    print(json.dumps(audit(), ensure_ascii=True, indent=2))
