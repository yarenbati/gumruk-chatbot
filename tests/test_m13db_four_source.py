"""Offline metrics, metadata identity, production-path and approval gate tests."""
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import run_m13db_four_source as runner


def _question() -> dict:
    return {'id': 'test-mixed', 'question': 'Exact unchanged question?',
            'expected_source_keys': ['gumruk_yonetmeligi/normal/496', 'gumruk_yonetmeligi/annex/77/c'],
            'expected_document_ids': ['gumruk_yonetmeligi']}


def _chunk(rank: int, article: str = '496', document: str = 'gumruk_yonetmeligi', annex: bool = False) -> SimpleNamespace:
    metadata = {'document_id': document, 'article_type': 'normal', 'article_no': article}
    if annex:
        metadata = {'document_id': document, 'source_type': 'annex', 'annex_no': 77,
                    'annex_subpart': 'C', 'annex_source_key': f'{document}/annex/77/c'}
    return SimpleNamespace(rank=rank, chunk_id='deliberately-unrelated-id', metadata=metadata, distance=0.1 * rank)


def test_mixed_metrics_keep_chunk_slots_and_each_expected_rank() -> None:
    rows = [_chunk(1, '1', '4458_gumruk_kanunu'), _chunk(2), _chunk(3), _chunk(4, '27'), _chunk(5, annex=True)]
    result = runner.score(_question(), rows)
    assert (result['hit@1'], result['hit@3'], result['hit@5']) == (False, True, True)
    assert result['reciprocal_rank@5'] == 0.5
    assert list(result['expected_source_ranks'].values()) == [2, 5]
    assert result['recall@5'] == 1 and result['full_coverage@5'] is True
    assert result['both_expected_sources@5'] is True
    assert result['wrong_document_count@5'] == 1
    assert result['wrong_document_fraction@5'] == 0.2
    partial = runner.score(_question(), rows[:4])
    assert partial['recall@5'] == 0.5
    assert partial['both_expected_sources@5'] is False
    assert partial['expected_source_ranks']['gumruk_yonetmeligi/annex/77/c'] is None
    empty = runner.score(_question(), [])
    assert empty['reciprocal_rank@5'] == 0 and empty['recall@5'] == 0
    assert empty['wrong_document_fraction@5'] is None
    summary = runner.summarize([result, partial])
    assert summary['mixed']['questions'] == 2
    assert summary['mixed']['recall@5'] == 0.75
    assert summary['mixed']['full_coverage@5'] == 0.5
    assert summary['mixed']['both_expected_sources@5_count'] == 1


def test_identity_is_metadata_only_and_rejects_malformed_annex() -> None:
    annex = _chunk(1, annex=True)
    assert runner.canonical_key(annex.metadata) == 'gumruk_yonetmeligi/annex/77/c'
    annex.metadata['annex_source_key'] = 'gumruk_yonetmeligi/annex/77/a'
    with pytest.raises(ValueError, match='mismatch'):
        runner.score(_question(), [annex])
    with pytest.raises(KeyError):
        runner.canonical_key({'document_id': 'gumruk_yonetmeligi', 'chunk_id': 'gumruk_yonetmeligi-ek-77-c-chunk-001'})
    with pytest.raises(ValueError, match='source_type'):
        runner.canonical_key({'document_id': 'gumruk_yonetmeligi', 'annex_no': 77, 'article_type': 'normal', 'article_no': '1'})
    with pytest.raises(ValueError, match='sequential'):
        runner.score(_question(), [_chunk(2)])


def test_api_gate_precedes_preflight_and_client_creation(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden() -> None:
        pytest.fail('Preflight must not run before approval gate')
    monkeypatch.setattr(runner, 'prepare', forbidden)
    monkeypatch.setenv('RUN_OPENAI_INTEGRATION_TESTS', '0')
    with pytest.raises(ValueError, match='approval'):
        runner.execute(approved=True)
    monkeypatch.setenv('RUN_OPENAI_INTEGRATION_TESTS', '1')
    with pytest.raises(ValueError, match='approval'):
        runner.execute()


def test_runner_uses_real_production_path_with_fake_external_boundaries(tmp_path: Path) -> None:
    requests = []
    queries = []

    class FakeEmbeddings:
        def create(self, **kwargs: object) -> SimpleNamespace:
            requests.append(kwargs)
            return SimpleNamespace(data=[SimpleNamespace(index=0, embedding=[0.0] * 1536)],
                                   usage=SimpleNamespace(prompt_tokens=7, total_tokens=7))

    class FakeCollection:
        configuration_json = {'hnsw': {'space': 'l2'}}

        def count(self) -> int:
            return 1266

        def query(self, **kwargs: object) -> dict:
            queries.append(kwargs)
            ranks = [_chunk(i, annex=i == 5) for i in range(1, 6)]
            return {'ids': [[f'id-{i}' for i in range(5)]], 'documents': [['fixture'] * 5],
                    'metadatas': [[r.metadata for r in ranks]], 'distances': [[r.distance for r in ranks]]}

    client = SimpleNamespace(embeddings=FakeEmbeddings())
    results = runner.run_questions([_question()], FakeCollection(), client, tmp_path)
    assert requests == [{'model': 'text-embedding-3-small', 'input': ['Exact unchanged question?']}]
    assert len(queries) == 1
    assert queries[0] == {'query_embeddings': [[0.0] * 1536], 'n_results': 5,
                          'where': None, 'include': ['documents', 'metadatas', 'distances']}
    assert results[0]['full_coverage@5'] is True
    assert results[0]['embedding_usage']['total_tokens'] == 7
    with pytest.raises(ValueError, match='Prior attempt'):
        runner.run_questions([_question()], FakeCollection(), client, tmp_path)
    assert len(requests) == 1
