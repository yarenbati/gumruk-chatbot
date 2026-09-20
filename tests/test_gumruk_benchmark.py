"""Offline preserved-question contract and identity/evidence gates for M13D-A."""
from copy import deepcopy
import hashlib
import json

import pytest

from scripts.audit_gumruk_benchmark import DATASET, source_key, validate_dataset


def test_preserved_benchmark_contract() -> None:
    text = DATASET.read_text(encoding='utf-8')
    data = json.loads(text)
    # Preserve the pre-remediation contract without freezing editable evidence.
    projection = {**data, 'questions': [{k: v for k, v in q.items() if k != 'evidence'}
                                      for q in data['questions']]}
    assert hashlib.sha256(json.dumps(projection, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest() == '7013b0d4dfb1d274c8dfe50111890e15a8a2334a17fe61eb33cab342498bacc7'
    # Pure schema fixture; actual corpus membership/text is audited separately.
    texts: dict[str, str] = {}
    for question in data['questions']:
        for key, excerpt in question['evidence'].items():
            texts[key] = texts.get(key, '') + '\n' + excerpt
    result = validate_dataset(data, texts)
    assert result['composition'] == {'article_only': 14, 'annex_only': 10, 'mixed': 6, 'multi_source': 6}
    assert result['distinct_expected_keys'] == 32
    missing = dict(texts)
    del missing['gumruk_yonetmeligi/annex/77/c']
    with pytest.raises(ValueError, match='Missing indexed source'):
        validate_dataset(data, missing)
    changed = deepcopy(data)
    changed['questions'][0]['evidence']['gumruk_yonetmeligi/normal/1'] = 'unsupported invented evidence'
    with pytest.raises(ValueError, match='Evidence not found'):
        validate_dataset(changed, texts)


def test_annex_identity_fails_closed() -> None:
    metadata = {'document_id': 'gumruk_yonetmeligi', 'source_type': 'annex',
                'annex_no': 77, 'annex_subpart': 'A', 'annex_source_key': 'gumruk_yonetmeligi/annex/77/a'}
    assert source_key(metadata) == 'gumruk_yonetmeligi/annex/77/a'
    with pytest.raises(ValueError, match='annex key mismatch'):
        source_key({**metadata, 'annex_source_key': 'gumruk_yonetmeligi/annex/77/b'})
    with pytest.raises(ValueError, match='Noncanonical'):
        source_key({**metadata, 'legislation_number': '4458'})


def test_article_identity_preserves_namespace() -> None:
    metadata = {'document_id': 'gumruk_yonetmeligi', 'article_type': 'normal', 'article_no': '72/Ç'}
    assert source_key(metadata) == 'gumruk_yonetmeligi/normal/72/Ç'
    assert source_key({**metadata, 'article_type': 'gecici', 'article_no': '3'}) == 'gumruk_yonetmeligi/gecici/3'
