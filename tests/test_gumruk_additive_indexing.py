"""Offline response alignment, preservation, and fail-closed indexing gates."""
from copy import deepcopy
from types import SimpleNamespace

import pytest

from scripts.index_gumruk_yonetmeligi import embed_batch, validate_vectors, verify_final


def test_embedding_response_reorders_indices_and_pins_model() -> None:
    class FakeEmbeddings:
        def create(self, **kwargs: object) -> SimpleNamespace:
            assert kwargs == {'model': 'text-embedding-3-small', 'input': ['a', 'b'], 'dimensions': 1536}
            return SimpleNamespace(model='text-embedding-3-small', data=[SimpleNamespace(index=1, embedding=[2.0] * 1536), SimpleNamespace(index=0, embedding=[1.0] * 1536)], usage=SimpleNamespace(prompt_tokens=2, total_tokens=2))

    vectors, usage = embed_batch(SimpleNamespace(embeddings=FakeEmbeddings()), ['a', 'b'])
    assert vectors[0][0] == 1.0 and vectors[1][0] == 2.0
    assert usage['total_tokens'] == 2


@pytest.mark.parametrize('vector', [[0.0], [float('nan')] * 1536, [True] * 1536])
def test_invalid_vectors_fail_closed(vector: list[float]) -> None:
    with pytest.raises(ValueError):
        validate_vectors([vector], 1)


def test_duplicate_api_indices_fail_closed() -> None:
    response = SimpleNamespace(model='text-embedding-3-small', data=[SimpleNamespace(index=0), SimpleNamespace(index=0)])
    client = SimpleNamespace(embeddings=SimpleNamespace(create=lambda **kwargs: response))
    with pytest.raises(ValueError, match='alignment'):
        embed_batch(client, ['a', 'b'])


def test_preservation_and_final_distribution_include_original_vectors() -> None:
    vector = [0.1] * 1536
    baseline = {f'{law}-{i}': {'document': 'original', 'metadata': {'legislation_number': law}, 'embedding': vector}
                for law, count in [('5326', 53), ('4458', 276), ('5607', 46)] for i in range(count)}
    new = [{'id': f'gumruk_yonetmeligi-{i}', 'document': 'new', 'metadata': {'document_id': 'gumruk_yonetmeligi'}} for i in range(891)]
    current = {**baseline, **{r['id']: {'document': r['document'], 'metadata': r['metadata'], 'embedding': vector} for r in new}}
    assert verify_final(current, baseline, new, [vector] * 891)['gumruk_yonetmeligi'] == 891
    changed = deepcopy(current)
    changed['5326-0']['embedding'][0] = 0.2
    with pytest.raises(ValueError, match='Historical'):
        verify_final(changed, baseline, new, [vector] * 891)
