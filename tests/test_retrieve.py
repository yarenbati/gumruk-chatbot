"""Tests for src/retrieve.py (M5A semantic retrieval service).

All tests are self-contained: they never call OpenAI, never require
`OPENAI_API_KEY`, and never make network calls. Vector-search correctness
tests use a real, local Chroma `PersistentClient` rooted at pytest's
`tmp_path` (never the project's real `chroma/` directory) populated via
`index.index_chunks` with small deterministic fake vectors. Response-shape /
call-argument tests use a minimal `_FakeQueryCollection` stand-in that gives
full control over what a Chroma `.query()` call returns, since a real Chroma
instance cannot easily be coerced into returning a malformed response.
Query-embedding tests use a fake OpenAI client (`_FakeClient`, mirroring
`tests/test_embed.py`) rather than a real one.

tests/questions.json is NOT read or used here - it belongs to the upcoming
M5B Recall@K evaluation (see that file's module-level notes / the M5A task
scope). This file only proves the retrieval mechanics work in isolation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from src import config, embed, index, retrieve
from src.chunk import Chunk

# ============================================================================
# Fixture helpers
# ============================================================================


def _c(
    chunk_id: str = "5326-madde-2-chunk-001",
    article_no: str = "2",
    *,
    article_id: str | None = None,
    article_type: str = "normal",
    article_title: str | None = "Tanım",
    section_context: str | None = "Birinci Kısım > Birinci Bölüm",
    text: str = "Madde 2- (1) Kabahat deyiminden idarî yaptırım anlaşılır.",
    document_id: str | None = "5326_kabahatler_kanunu",
    legislation_number: str | None = "5326",
    paragraph_numbers: list[str] | None = None,
    source_paragraph_start: int = 22,
    source_paragraph_end: int = 22,
    footnote_references: list[int] | None = None,
) -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        article_id=article_id or f"5326-madde-{article_no.lower().replace('/', '-')}",
        document_id=document_id,
        legislation_number=legislation_number,
        article_no=article_no,
        article_type=article_type,
        article_title=article_title,
        section_context=section_context,
        text=text,
        paragraph_numbers=paragraph_numbers,
        source_paragraph_start=source_paragraph_start,
        source_paragraph_end=source_paragraph_end,
        footnote_references=footnote_references,
    )


def _fresh_collection(tmp_path: Path, name: str = "test-retrieve"):
    client = index.get_client(tmp_path)
    return index.get_collection(client, name)


def _r(chunk_id: str, embedding: list[float], model: str = "fake-model") -> embed.EmbeddingResult:
    return embed.EmbeddingResult(chunk_id=chunk_id, embedding=embedding, model=model)


# ============================================================================
# Fake OpenAI client (mirrors tests/test_embed.py's _FakeClient)
# ============================================================================


class _FakeEmbeddingItem:
    def __init__(self, index: int, embedding: list[float]) -> None:
        self.index = index
        self.embedding = embedding


class _FakeUsage:
    def __init__(self, prompt_tokens: int, total_tokens: int) -> None:
        self.prompt_tokens = prompt_tokens
        self.total_tokens = total_tokens


class _FakeResponse:
    def __init__(self, data: list[_FakeEmbeddingItem], usage: _FakeUsage | None) -> None:
        self.data = data
        self.usage = usage


class _FakeEmbeddingsResource:
    def __init__(self, vector: list[float]) -> None:
        self._vector = vector
        self.calls: list[tuple[str, list[str]]] = []

    def create(self, *, model: str, input: list[str]) -> _FakeResponse:  # noqa: A002
        self.calls.append((model, list(input)))
        data = [_FakeEmbeddingItem(index=i, embedding=self._vector) for i in range(len(input))]
        return _FakeResponse(data=data, usage=_FakeUsage(prompt_tokens=3, total_tokens=3))


class _FakeClient:
    def __init__(self, vector: list[float]) -> None:
        self.embeddings = _FakeEmbeddingsResource(vector)


# ============================================================================
# Fake Chroma collection (full control over query() response/args)
# ============================================================================


class _FakeQueryCollection:
    """Minimal stand-in for a chromadb Collection: records every `.query()`
    call's kwargs and returns a caller-supplied response. Used only for
    response-alignment / call-shape tests that a real Chroma instance cannot
    easily be coerced into producing (e.g. a deliberately malformed
    response)."""

    def __init__(self, response: dict[str, Any], *, count: int = 1) -> None:
        self._response = response
        self._count = count
        self.metadata: dict[str, Any] | None = None
        self.configuration_json: dict[str, Any] = {}
        self.calls: list[dict[str, Any]] = []

    def count(self) -> int:
        return self._count

    def query(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        return self._response


def _empty_response() -> dict[str, Any]:
    return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}


# ============================================================================
# 1-5: input validation
# ============================================================================


def test_non_string_query_rejected(tmp_path: Path) -> None:
    _, collection = None, _fresh_collection(tmp_path)
    with pytest.raises(retrieve.RetrievalError):
        retrieve.retrieve(123, collection=collection, client=_FakeClient([1.0, 2.0]))  # type: ignore[arg-type]


def test_empty_query_rejected(tmp_path: Path) -> None:
    collection = _fresh_collection(tmp_path)
    with pytest.raises(retrieve.RetrievalError):
        retrieve.retrieve("", collection=collection, client=_FakeClient([1.0, 2.0]))


def test_whitespace_only_query_rejected(tmp_path: Path) -> None:
    collection = _fresh_collection(tmp_path)
    with pytest.raises(retrieve.RetrievalError):
        retrieve.retrieve("   \n\t  ", collection=collection, client=_FakeClient([1.0, 2.0]))


def test_top_k_zero_rejected(tmp_path: Path) -> None:
    collection = _fresh_collection(tmp_path)
    with pytest.raises(retrieve.RetrievalError):
        retrieve.retrieve("Kabahat nedir?", collection=collection, client=_FakeClient([1.0, 2.0]), top_k=0)


def test_top_k_negative_rejected(tmp_path: Path) -> None:
    collection = _fresh_collection(tmp_path)
    with pytest.raises(retrieve.RetrievalError):
        retrieve.retrieve("Kabahat nedir?", collection=collection, client=_FakeClient([1.0, 2.0]), top_k=-1)


# ============================================================================
# 6-7: empty / undersized collection
# ============================================================================


def test_empty_collection_returns_zero_results(tmp_path: Path) -> None:
    collection = _fresh_collection(tmp_path)
    result = retrieve.retrieve("Kabahat nedir?", collection=collection, client=_FakeClient([1.0, 0.0, 0.0, 0.0]))
    assert result.returned_count == 0
    assert result.results == []


def test_empty_collection_never_calls_chroma_query(tmp_path: Path) -> None:
    fake_collection = _FakeQueryCollection(_empty_response(), count=0)
    results = retrieve.retrieve_by_embedding([1.0, 0.0], collection=fake_collection, top_k=5)
    assert results == []
    assert fake_collection.calls == []  # short-circuited before ever querying Chroma


def test_collection_smaller_than_top_k_returns_only_available_records(tmp_path: Path) -> None:
    collection = _fresh_collection(tmp_path)
    chunks = [_c(chunk_id=f"c-{i}", article_no=str(i)) for i in range(3)]
    results = [_r(c.chunk_id, [float(i), 0.0, 0.0, 0.0]) for i, c in enumerate(chunks)]
    index.index_chunks(chunks, results, collection=collection)

    out = retrieve.retrieve_by_embedding([0.0, 0.0, 0.0, 0.0], collection=collection, top_k=5)
    assert len(out) == 3  # never fabricates 2 extra results


def test_top_k_capped_to_collection_count_in_chroma_call() -> None:
    response = {
        "ids": [["a", "b", "c"]],
        "documents": [["x", "y", "z"]],
        "metadatas": [[{}, {}, {}]],
        "distances": [[0.1, 0.2, 0.3]],
    }
    fake_collection = _FakeQueryCollection(response, count=3)
    retrieve.retrieve_by_embedding([1.0], collection=fake_collection, top_k=5)
    assert fake_collection.calls[0]["n_results"] == 3


# ============================================================================
# 8-16, 26: vector-search correctness (real tmp_path Chroma, fake vectors)
# ============================================================================


def _populate_ranking_fixture(tmp_path: Path):
    """Three chunks with orthogonal 4-D vectors, inserted in an order that
    differs from their eventual nearest-neighbor rank - proves result
    ordering/alignment comes from Chroma's own ranking, not insertion order.
    """
    collection = _fresh_collection(tmp_path)
    chunk_a = _c(chunk_id="c-A", article_no="10", paragraph_numbers=["1", "2"])
    chunk_b = _c(chunk_id="c-B", article_no="20", text="Madde 20 metni.")
    chunk_c = _c(chunk_id="c-C", article_no="30", footnote_references=[7, 9])

    # Insertion order: C, A, B - deliberately not the nearest-neighbor order.
    chunks = [chunk_c, chunk_a, chunk_b]
    vectors = {
        "c-A": [1.0, 0.0, 0.0, 0.0],
        "c-B": [0.0, 1.0, 0.0, 0.0],
        "c-C": [0.0, 0.0, 1.0, 0.0],
    }
    results = [_r(c.chunk_id, vectors[c.chunk_id]) for c in chunks]
    index.index_chunks(chunks, results, collection=collection)

    # Closest to c-B (dist~0.02), then c-C (dist~1.62), then c-A (dist~1.82).
    query_vector = [0.0, 0.9, 0.1, 0.0]
    return collection, chunk_a, chunk_b, chunk_c, query_vector


def test_nearest_vector_is_rank_1(tmp_path: Path) -> None:
    collection, _a, chunk_b, _c_, query_vector = _populate_ranking_fixture(tmp_path)
    out = retrieve.retrieve_by_embedding(query_vector, collection=collection, top_k=3)
    assert out[0].rank == 1
    assert out[0].chunk_id == chunk_b.chunk_id


def test_result_ordering_follows_chroma_ordering(tmp_path: Path) -> None:
    collection, chunk_a, chunk_b, chunk_c, query_vector = _populate_ranking_fixture(tmp_path)
    out = retrieve.retrieve_by_embedding(query_vector, collection=collection, top_k=3)
    assert [r.chunk_id for r in out] == [chunk_b.chunk_id, chunk_c.chunk_id, chunk_a.chunk_id]


def test_ranks_are_sequential_starting_at_one(tmp_path: Path) -> None:
    collection, *_rest, query_vector = _populate_ranking_fixture(tmp_path)
    out = retrieve.retrieve_by_embedding(query_vector, collection=collection, top_k=3)
    assert [r.rank for r in out] == [1, 2, 3]


def test_chunk_id_returned_exactly(tmp_path: Path) -> None:
    collection, _a, chunk_b, _c_, query_vector = _populate_ranking_fixture(tmp_path)
    out = retrieve.retrieve_by_embedding(query_vector, collection=collection, top_k=1)
    assert out[0].chunk_id == "c-B"


def test_stored_chunk_text_returned_exactly(tmp_path: Path) -> None:
    collection, _a, chunk_b, _c_, query_vector = _populate_ranking_fixture(tmp_path)
    out = retrieve.retrieve_by_embedding(query_vector, collection=collection, top_k=1)
    assert out[0].text == chunk_b.text


def test_correct_metadata_paired_with_correct_chunk(tmp_path: Path) -> None:
    collection, chunk_a, chunk_b, chunk_c, query_vector = _populate_ranking_fixture(tmp_path)
    out = retrieve.retrieve_by_embedding(query_vector, collection=collection, top_k=3)
    by_id = {r.chunk_id: r for r in out}
    assert by_id["c-A"].metadata["article_no"] == "10"
    assert by_id["c-B"].metadata["article_no"] == "20"
    assert by_id["c-C"].metadata["article_no"] == "30"


def test_paragraph_numbers_list_survives_retrieval(tmp_path: Path) -> None:
    collection, chunk_a, _b, _c_, query_vector = _populate_ranking_fixture(tmp_path)
    out = retrieve.retrieve_by_embedding(query_vector, collection=collection, top_k=3)
    by_id = {r.chunk_id: r for r in out}
    assert by_id["c-A"].metadata["paragraph_numbers"] == ["1", "2"]
    assert "paragraph_numbers" not in by_id["c-B"].metadata


def test_footnote_references_list_survives_retrieval(tmp_path: Path) -> None:
    collection, _a, _b, chunk_c, query_vector = _populate_ranking_fixture(tmp_path)
    out = retrieve.retrieve_by_embedding(query_vector, collection=collection, top_k=3)
    by_id = {r.chunk_id: r for r in out}
    assert by_id["c-C"].metadata["footnote_references"] == [7, 9]
    assert "footnote_references" not in by_id["c-B"].metadata


def test_distances_are_numeric_raw_values(tmp_path: Path) -> None:
    collection, *_rest, query_vector = _populate_ranking_fixture(tmp_path)
    out = retrieve.retrieve_by_embedding(query_vector, collection=collection, top_k=3)
    for r in out:
        assert isinstance(r.distance, float)
    # Never converted into a made-up 0-1 similarity/confidence score.
    assert out[0].distance < out[1].distance < out[2].distance


def test_different_insertion_order_still_aligns_metadata_and_documents(tmp_path: Path) -> None:
    """Regression guard for the exact bug class §12 defends against: nothing
    here assumes Chroma's result order equals insertion order."""
    collection, chunk_a, chunk_b, chunk_c, query_vector = _populate_ranking_fixture(tmp_path)
    out = retrieve.retrieve_by_embedding(query_vector, collection=collection, top_k=3)
    by_id = {r.chunk_id: r for r in out}
    assert by_id["c-A"].text == chunk_a.text
    assert by_id["c-B"].text == chunk_b.text
    assert by_id["c-C"].text == chunk_c.text


# ============================================================================
# 17-20: query embedding contract
# ============================================================================


def test_retrieve_uses_config_embedding_model_by_default(tmp_path: Path) -> None:
    collection = _fresh_collection(tmp_path)
    fake_client = _FakeClient([1.0, 0.0, 0.0, 0.0])
    result = retrieve.retrieve("Kabahat nedir?", collection=collection, client=fake_client)
    assert result.model == config.EMBEDDING_MODEL
    assert fake_client.embeddings.calls[0][0] == config.EMBEDDING_MODEL


def test_raw_user_question_sent_to_embedding_layer(tmp_path: Path) -> None:
    collection = _fresh_collection(tmp_path)
    fake_client = _FakeClient([1.0, 0.0, 0.0, 0.0])
    question = "Kabahatlerde soruşturma zamanaşımı nasıl belirlenir?"
    retrieve.retrieve(question, collection=collection, client=fake_client)
    _model, sent_inputs = fake_client.embeddings.calls[0]
    assert sent_inputs == [question]


def test_build_embedding_text_not_used_for_query(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def _forbidden(*_args: Any, **_kwargs: Any) -> str:
        raise AssertionError("build_embedding_text() must not be called for a user query")

    monkeypatch.setattr(embed, "build_embedding_text", _forbidden)

    collection = _fresh_collection(tmp_path)
    fake_client = _FakeClient([1.0, 0.0, 0.0, 0.0])
    retrieve.retrieve("Kabahate teşebbüs cezalandırılır mı?", collection=collection, client=fake_client)


def test_query_embedding_contains_exactly_one_vector() -> None:
    vector, model, usage = retrieve.embed_query("Kabahat nedir?", client=_FakeClient([1.0, 2.0, 3.0]))
    assert vector == [1.0, 2.0, 3.0]
    assert model  # a model name was recorded
    assert usage.prompt_tokens == 3


# ============================================================================
# 21-25: defensive Chroma response handling / call shape
# ============================================================================


def test_malformed_chroma_alignment_raises_retrieval_error() -> None:
    response = {
        "ids": [["a", "b"]],
        "documents": [["docA"]],  # one short - misaligned with ids
        "metadatas": [[{}, {}]],
        "distances": [[0.1, 0.2]],
    }
    fake_collection = _FakeQueryCollection(response, count=2)
    with pytest.raises(retrieve.RetrievalError):
        retrieve.retrieve_by_embedding([1.0], collection=fake_collection, top_k=2)


def test_optional_where_filter_passed_through() -> None:
    response = {"ids": [["a"]], "documents": [["x"]], "metadatas": [[{}]], "distances": [[0.1]]}
    fake_collection = _FakeQueryCollection(response, count=1)
    where = {"legislation_number": "5326"}
    retrieve.retrieve_by_embedding([1.0], collection=fake_collection, top_k=1, where=where)
    assert fake_collection.calls[0]["where"] == where


def test_default_where_filter_is_none() -> None:
    response = {"ids": [["a"]], "documents": [["x"]], "metadatas": [[{}]], "distances": [[0.1]]}
    fake_collection = _FakeQueryCollection(response, count=1)
    retrieve.retrieve_by_embedding([1.0], collection=fake_collection, top_k=1)
    assert fake_collection.calls[0]["where"] is None


def test_fake_client_and_fake_collection_path_requires_no_api_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(config, "OPENAI_API_KEY", None)
    collection = _fresh_collection(tmp_path)
    fake_client = _FakeClient([1.0, 0.0, 0.0, 0.0])
    result = retrieve.retrieve("Kabahat nedir?", collection=collection, client=fake_client)
    assert result.returned_count == 0  # empty collection, but no error - proves no API key was needed


def test_query_uses_query_embeddings_not_query_texts() -> None:
    fake_collection = _FakeQueryCollection(_empty_response(), count=1)
    retrieve.retrieve_by_embedding([1.0, 2.0], collection=fake_collection, top_k=1)
    call = fake_collection.calls[0]
    assert "query_embeddings" in call
    assert call["query_embeddings"] == [[1.0, 2.0]]
    assert "query_texts" not in call


def test_query_does_not_request_stored_embedding_vectors() -> None:
    fake_collection = _FakeQueryCollection(_empty_response(), count=1)
    retrieve.retrieve_by_embedding([1.0, 2.0], collection=fake_collection, top_k=1)
    assert "embeddings" not in fake_collection.calls[0]["include"]
    assert set(fake_collection.calls[0]["include"]) == {"documents", "metadatas", "distances"}
