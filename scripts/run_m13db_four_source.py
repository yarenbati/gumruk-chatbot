"""M13D-B: unchanged dense retrieval, metadata-only identities, explicit API gate."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import config, retrieve
from src.source_identity import AnnexSourceKey, DocumentSourceKey

ROOT = Path(__file__).resolve().parents[1]
BASELINE = 'fb4ee67f272fc2cda7c3063c8912d065d59ed034'
DATASET = ROOT / 'evaluation/questions_gumruk_yonetmeligi.json'
DATASET_SHA256 = '63d296bcf1a02f7494f6469fc3aff479f96ab7c8ce2725843e95e470c6577a08'
REPORT = ROOT / 'reports/evaluation'
STATE = ROOT / 'data/processed/m13db-retrieval'
EXPECTED_DISTRIBUTION = {'5326_kabahatler_kanunu': 53, '4458_gumruk_kanunu': 276,
                         '5607_kacakcilikla_mucadele_kanunu': 46, 'gumruk_yonetmeligi': 891}
OWN_FILES = {'scripts/run_m13db_four_source.py', 'tests/test_m13db_four_source.py',
             'reports/evaluation/m13db-preflight.json', 'reports/evaluation/m13db-execution-plan.md'}


def canonical_key(metadata: dict[str, Any]) -> str:
    """Derive identity only from metadata, rejecting malformed annex provenance."""
    document = metadata['document_id']
    if metadata.get('source_type') == 'annex':
        key = AnnexSourceKey(document, metadata['annex_no'], metadata.get('annex_subpart') or None)
        if metadata.get('annex_source_key') != str(key):
            raise ValueError('Annex canonical key mismatch')
        return str(key)
    if any(name in metadata for name in ('annex_no', 'annex_source_key', 'annex_subpart')):
        raise ValueError('Annex metadata without annex source_type')
    return str(DocumentSourceKey(document, metadata['article_type'], metadata['article_no']))


def question_type(question: dict[str, Any]) -> str:
    """Classify by the frozen expected keys without modifying the dataset."""
    keys = question['expected_source_keys']
    count = sum('/annex/' in key for key in keys)
    return 'annex' if count == len(keys) else 'mixed' if count else 'article'


def score(question: dict[str, Any], chunks: list[Any]) -> dict[str, Any]:
    """Score original top-five chunk slots; duplicate sources never promote ranks."""
    if len(chunks) > 5 or [c.rank for c in chunks] != list(range(1, len(chunks) + 1)):
        raise ValueError('Expected sequential top-five ranks')
    expected = question['expected_source_keys']
    ranked = [{'rank': c.rank, 'chunk_id': c.chunk_id, 'source_key': canonical_key(c.metadata),
               'document_id': c.metadata['document_id'], 'distance': c.distance} for c in chunks]
    source_ranks = {key: next((r['rank'] for r in ranked if r['source_key'] == key), None) for key in expected}
    found = [rank for rank in source_ranks.values() if rank is not None]
    first = min(found) if found else None
    wrong = [r for r in ranked if r['document_id'] not in question['expected_document_ids']]
    return {'id': question['id'], 'type': question_type(question), 'question': question['question'],
            'expected_keys': expected, 'retrieved': ranked, 'expected_source_ranks': source_ranks,
            **{f'hit@{k}': first is not None and first <= k for k in (1, 3, 5)},
            'reciprocal_rank@5': 1 / first if first else 0.0,
            'recall@5': len(found) / len(expected), 'full_coverage@5': len(found) == len(expected),
            'both_expected_sources@5': len(found) == 2 if question_type(question) == 'mixed' else None,
            'wrong_document_count@5': len(wrong),
            'wrong_document_fraction@5': len(wrong) / len(ranked) if ranked else None,
            'wrong_document_ranks': [r['rank'] for r in wrong]}


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute macro metrics overall and in the three disjoint question groups."""
    summary = {}
    for group in ('overall', 'article', 'annex', 'mixed'):
        rows = results if group == 'overall' else [r for r in results if r['type'] == group]
        if not rows:
            summary[group] = {'questions': 0}
            continue
        metrics = {name: sum(r[name] for r in rows) / len(rows) for name in
                   ('hit@1', 'hit@3', 'hit@5', 'recall@5', 'full_coverage@5')}
        slots = sum(len(r['retrieved']) for r in rows)
        wrong = sum(r['wrong_document_count@5'] for r in rows)
        summary[group] = {'questions': len(rows), **metrics,
                          'MRR@5': sum(r['reciprocal_rank@5'] for r in rows) / len(rows),
                          'wrong_document_results@5': wrong, 'retrieved_slots': slots,
                          'wrong_document_fraction@5': wrong / slots if slots else None,
                          'questions_with_wrong_document@5': sum(r['wrong_document_count@5'] > 0 for r in rows)}
        if group == 'mixed':
            summary[group]['both_expected_sources@5_count'] = sum(r['both_expected_sources@5'] for r in rows)
    return summary


def fingerprints(directory: Path) -> dict[str, str]:
    """Read hashes of all storage files without constructing a Chroma client."""
    return {p.relative_to(directory).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(directory.rglob('*')) if p.is_file()}


def prepare() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Validate baseline, immutable corpus and frozen gold with zero API calls."""
    def git(*args: str) -> str:
        return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()
    if git('rev-parse', 'HEAD') != BASELINE or git('rev-parse', 'origin/main') != BASELINE:
        raise ValueError('Baseline/origin mismatch')
    changed = set(git('diff', '--name-only', 'HEAD').splitlines()) | set(git('ls-files', '--others', '--exclude-standard').splitlines())
    if changed - OWN_FILES:
        raise ValueError(f'Unrelated changes: {sorted(changed - OWN_FILES)}')
    if hashlib.sha256(DATASET.read_bytes()).hexdigest() != DATASET_SHA256:
        raise ValueError('Frozen dataset hash mismatch')
    questions = json.loads(DATASET.read_text(encoding='utf-8'))['questions']
    if len(questions) != 30 or dict(Counter(question_type(q) for q in questions)) != {'article': 14, 'annex': 10, 'mixed': 6}:
        raise ValueError('Frozen composition mismatch')
    if config.EMBEDDING_MODEL != 'text-embedding-3-small' or config.TOP_K != 5:
        raise ValueError('Production model or TOP_K changed')
    production = (ROOT / config.CHROMA_PATH).resolve()
    database = production / 'chroma.sqlite3'
    if not database.is_file() or Path(str(database) + '-wal').exists():
        raise ValueError('Stable checkpointed production required')
    before = fingerprints(production)
    connection = sqlite3.connect(database.as_uri() + '?mode=ro&immutable=1', uri=True)
    distribution: Counter[str] = Counter()
    keys: set[str] = set()
    try:
        rows = connection.execute('SELECT e.id FROM embeddings e JOIN segments s ON e.segment_id=s.id '
                                  'JOIN collections c ON s.collection=c.id WHERE c.name=?', (config.COLLECTION_NAME,)).fetchall()
        for internal, in rows:
            metadata = {key: string if string is not None else integer for key, string, integer in
                        connection.execute('SELECT key,string_value,int_value FROM embedding_metadata WHERE id=?', (internal,))}
            keys.add(canonical_key(metadata))
            distribution[metadata['document_id']] += 1
    finally:
        connection.close()
    if len(rows) != 1266 or dict(distribution) != EXPECTED_DISTRIBUTION:
        raise ValueError('Production count/distribution mismatch')
    if not {key for q in questions for key in q['expected_source_keys']} <= keys:
        raise ValueError('Expected sources missing from production')
    if before != fingerprints(production):
        raise ValueError('Production changed during preflight')
    return {'baseline': BASELINE, 'dataset_sha256': DATASET_SHA256, 'collection': config.COLLECTION_NAME,
            'production_count': len(rows), 'distribution': dict(distribution), 'production_fingerprints': before,
            'model': config.EMBEDDING_MODEL, 'top_k': config.TOP_K,
            'questions': 30, 'groups': {'article': 14, 'annex': 10, 'mixed': 6},
            'planned_embedding_requests': 30, 'planned_dense_queries': 30, 'generation_requests': 0,
            'network_calls_performed': 0, 'status': 'AWAITING_API_APPROVAL'}, questions


def write_json(path: Path, value: Any) -> None:
    """Atomically save local evaluation artifacts, never Chroma records."""
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def run_questions(questions: list[dict[str, Any]], collection: Any, client: Any,
                  state: Path) -> list[dict[str, Any]]:
    """Call the unmodified production entrypoint once per raw question; checkpoint."""
    results = []
    for question in questions:
        attempt = state / f'{question["id"]}.attempt.json'
        completed = state / f'{question["id"]}.json'
        if attempt.exists() or completed.exists():
            raise ValueError('Prior attempt exists; manual review required before any retry')
        write_json(attempt, {'id': question['id'], 'dataset_sha256': DATASET_SHA256})
        response = retrieve.retrieve(question['question'], collection=collection, client=client,
                                     model=config.EMBEDDING_MODEL, top_k=config.TOP_K)
        result = score(question, response.results)
        result.update(embedding_usage=asdict(response.embedding_usage), latency_ms=response.latency_ms,
                      distance_metric=response.distance_metric)
        write_json(completed, result)
        results.append(result)
    return results


def execute(*, approved: bool = False) -> dict[str, Any]:
    """Run only after explicit external approval and the separate environment gate."""
    if not approved or os.getenv('RUN_OPENAI_INTEGRATION_TESTS') != '1':
        raise ValueError('Explicit API approval and RUN_OPENAI_INTEGRATION_TESTS=1 required')
    plan, questions = prepare()
    if STATE.exists() or (REPORT / 'm13db-four-source-retrieval.json').exists():
        raise ValueError('Existing run state/report; refusing automatic rerun')
    if not config.OPENAI_API_KEY:
        raise ValueError('Missing API key')
    # A byte-identical disposable copy prevents Chroma startup/migration writes
    # from touching production. No add/upsert/delete/reset/create operations.
    production = (ROOT / config.CHROMA_PATH).resolve()
    destination = Path(tempfile.mkdtemp(prefix='m13db-chroma-copy-')) / 'chroma'
    shutil.copytree(production, destination)
    if fingerprints(destination) != plan['production_fingerprints'] or fingerprints(production) != plan['production_fingerprints']:
        raise ValueError('Copy byte verification failed')
    import chromadb
    from chromadb.config import Settings
    from openai import OpenAI
    collection = chromadb.PersistentClient(path=str(destination), settings=Settings(anonymized_telemetry=False)).get_collection(config.COLLECTION_NAME, embedding_function=None)
    if collection.count() != 1266:
        raise ValueError('Copy count mismatch')
    STATE.mkdir(parents=True)
    write_json(STATE / 'plan.json', plan)
    try:
        # Disable transport retries solely for bounded spending/accounting.
        client = OpenAI(api_key=config.OPENAI_API_KEY, max_retries=0)
        results = run_questions(questions, collection, client, STATE)
        report = {'plan': plan, 'status': 'COMPLETED', 'summary': summarize(results), 'questions': results}
        write_json(REPORT / 'm13db-four-source-retrieval.json', report)
        fields = list(results[0])
        with (REPORT / 'm13db-four-source-retrieval.csv').open('w', encoding='utf-8-sig', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for row in results:
                writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for k, v in row.items()})
        return report
    finally:
        if fingerprints(production) != plan['production_fingerprints']:
            raise ValueError('Production storage changed during evaluation')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true', help='Requires user approval before use')
    args = parser.parse_args()
    if args.execute:
        print(json.dumps(execute(approved=True)['summary'], indent=2))
    else:
        plan, _ = prepare()
        write_json(REPORT / 'm13db-preflight.json', plan)
        print(json.dumps(plan, indent=2))
