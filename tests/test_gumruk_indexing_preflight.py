"""Offline safety gates and lossless annex metadata projection."""
import json
from pathlib import Path

import pytest

from scripts.preflight_gumruk_indexing import annex_chroma_metadata, plan_batches, production_ids, run
from src.annex_chunk import AnnexChunk


@pytest.mark.parametrize('count', [0, -1, 8193])
def test_unsafe_input_fails_closed(count: int) -> None:
    with pytest.raises(ValueError, match='Unsafe embedding input'):
        plan_batches([count], model='text-embedding-3-small')


def test_unknown_model_fails_closed() -> None:
    with pytest.raises(ValueError, match='Unreviewed'):
        plan_batches([1], model='unreviewed-model')


def test_batching_enforces_token_and_input_caps() -> None:
    batches = plan_batches([8192] * 65, model='text-embedding-3-small')
    assert [len(batch) for batch in batches] == [36, 29]
    assert [i for batch in batches for i in batch] == list(range(65))
    assert [len(batch) for batch in plan_batches([10] * 891, model='text-embedding-3-small')] == [64] * 13 + [59]


def test_annex_metadata_is_lossless_and_filterable() -> None:
    original = {'document_id': 'gumruk_yonetmeligi', 'source_type': 'annex',
                'annex_no': 33, 'annex_subpart': None,
                'source_members': [{'archive_member_path': 'EK 33.doc', 'normalization': {'normalized_sha256': 'abc'}}],
                'warnings': [], 'chunk_id': 'gumruk_yonetmeligi-ek-33-chunk-001'}
    piece = AnnexChunk(original['chunk_id'], 'body', (), original)
    metadata = annex_chroma_metadata(piece)
    assert json.loads(metadata['annex_metadata_json']) == original
    assert metadata['annex_no'] == 33
    assert 'annex_subpart' not in metadata
    assert 'legislation_number' not in metadata
    assert metadata == annex_chroma_metadata(piece)


def test_uncheckpointed_database_rejected_without_opening(tmp_path: Path) -> None:
    (tmp_path / 'chroma.sqlite3').write_bytes(b'fixture')
    (tmp_path / 'chroma.sqlite3-wal').write_bytes(b'pending')
    with pytest.raises(ValueError, match='checkpointed'):
        production_ids(tmp_path)


def test_real_preflight_never_constructs_clients(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError('External clients forbidden during preflight')

    monkeypatch.setattr('src.embed.OpenAI', forbidden)
    monkeypatch.setattr('chromadb.PersistentClient', forbidden)
    report = run()
    assert all(report['gates'].values())
    assert report['new_inputs'] == 891
    assert report['maximum_input_tokens'] == 5432
    assert report['production_vectors'] == 375
    assert report['expected_post_index_vectors'] == 1266
    assert report['proposed_batch_count'] == 14
