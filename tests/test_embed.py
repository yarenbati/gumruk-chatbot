"""Tests for src/embed.py (M4A OpenAI embedding service).

All core tests are self-contained and use a fake OpenAI client (see
`_FakeClient` below) - they never call the real OpenAI API and never require
`OPENAI_API_KEY`, matching docs/indexing.md §9's test strategy.

A separate, clearly-named integration section at the bottom calls the real
OpenAI API. Unlike the `data/raw/`-dependent integration tests in
test_ingest.py / test_chunk.py (which only need the source file to be
present), a real OpenAI call costs money and hits an external network
service - so it must never run just because a developer happens to have
`OPENAI_API_KEY` set in `.env`. These tests require BOTH of:

    OPENAI_API_KEY=<a real key>
    RUN_OPENAI_INTEGRATION_TESTS=1

and SKIP cleanly (not fail) whenever either is missing - in particular,
plain `python -m pytest -q` must make zero real API calls even when
`OPENAI_API_KEY` is present, since `RUN_OPENAI_INTEGRATION_TESTS` is unset
by default. `@pytest.mark.skipif` alone is not relied on for this, since
that only changes reporting/collection, not what a bare `pytest -q` will
execute - the underlying condition is a real opt-in env var, not just a
marker name a developer would have to remember to deselect.

To run them explicitly:

    RUN_OPENAI_INTEGRATION_TESTS=1 python -m pytest -q tests/test_embed.py -m integration

They never print the API key or full embedding vectors.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from src import config, embed
from src.chunk import Chunk

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REAL_CHUNKS_PATH = PROJECT_ROOT / "data" / "processed" / "5326-kabahatler-kanunu.chunks.json"

_INTEGRATION_OPT_IN = os.getenv("RUN_OPENAI_INTEGRATION_TESTS") == "1"
_REAL_API_AVAILABLE = bool(config.OPENAI_API_KEY) and _INTEGRATION_OPT_IN
_SKIP_REASON = (
    "real OpenAI integration test: requires both OPENAI_API_KEY and "
    "RUN_OPENAI_INTEGRATION_TESTS=1 (never runs under a plain `pytest -q`)"
)


# ============================================================================
# Fake OpenAI client
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
    """Records every call (model, input list) and delegates the response to
    a caller-supplied `responder(model, input) -> _FakeResponse` function."""

    def __init__(self, responder) -> None:
        self._responder = responder
        self.calls: list[tuple[str, list[str]]] = []

    def create(self, *, model: str, input: list[str]) -> _FakeResponse:  # noqa: A002 - mirrors SDK kwarg name
        self.calls.append((model, list(input)))
        return self._responder(model, input)


class _FakeClient:
    def __init__(self, responder) -> None:
        self.embeddings = _FakeEmbeddingsResource(responder)


def _deterministic_vector(text: str, dim: int = 4) -> list[float]:
    """A cheap, deterministic stand-in vector derived from text length -
    real embedding semantics don't matter for these tests, only alignment."""
    return [float(len(text) + i) for i in range(dim)]


def _default_responder(dim: int = 4, prompt_tokens_per_input: int = 3):
    def responder(model: str, texts: list[str]) -> _FakeResponse:
        data = [_FakeEmbeddingItem(index=i, embedding=_deterministic_vector(t, dim)) for i, t in enumerate(texts)]
        usage = _FakeUsage(
            prompt_tokens=prompt_tokens_per_input * len(texts),
            total_tokens=prompt_tokens_per_input * len(texts),
        )
        return _FakeResponse(data=data, usage=usage)

    return responder


# ============================================================================
# Chunk fixture helper
# ============================================================================


def _c(
    chunk_id: str = "5326-madde-2-chunk-001",
    article_no: str = "2",
    *,
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
        article_id=f"5326-madde-{article_no.lower().replace('/', '-')}",
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


# --- Embedding text construction --------------------------------------------


def test_embedding_text_format_with_article_title() -> None:
    chunk = _c(article_title="Tanım", text="Madde 2- (1) Kabahat deyiminden idarî yaptırım anlaşılır.")
    text = embed.build_embedding_text(chunk)
    assert text == (
        "5326 Sayılı Kabahatler Kanunu\n"
        "Madde 2\n"
        "Tanım\n"
        "\n"
        "Madde 2- (1) Kabahat deyiminden idarî yaptırım anlaşılır."
    )


def test_embedding_text_format_without_article_title() -> None:
    chunk = _c(article_title=None, text="Ek Madde 1- (1) Ek madde hükmü metni.", article_no="1", article_type="ek")
    text = embed.build_embedding_text(chunk)
    assert text == (
        "5326 Sayılı Kabahatler Kanunu\n"
        "Ek Madde 1\n"
        "\n"
        "Ek Madde 1- (1) Ek madde hükmü metni."
    )
    assert "None" not in text


def test_embedding_text_never_modifies_chunk_text() -> None:
    original_text = "Madde 2- (1) Kabahat deyiminden idarî yaptırım anlaşılır."
    chunk = _c(text=original_text)
    embed.build_embedding_text(chunk)
    assert chunk.text == original_text  # frozen dataclass + no mutation


# --- Article labels -----------------------------------------------------------


def test_normal_article_label() -> None:
    assert embed.build_article_label("normal", "2") == "Madde 2"


def test_lettered_article_label() -> None:
    assert embed.build_article_label("normal", "42/A") == "Madde 42/A"


def test_ek_madde_label() -> None:
    assert embed.build_article_label("ek", "1") == "Ek Madde 1"


def test_gecici_madde_label() -> None:
    assert embed.build_article_label("gecici", "1") == "Geçici Madde 1"


def test_unknown_article_type_raises() -> None:
    with pytest.raises(ValueError):
        embed.build_article_label("unknown", "1")


# --- Display title derivation --------------------------------------------------


def test_display_title_derivation_from_manifest() -> None:
    title = embed.build_document_display_title("5326_kabahatler_kanunu", "5326")
    assert title == "5326 Sayılı Kabahatler Kanunu"


def test_display_title_does_not_duplicate_legislation_number_already_in_title(monkeypatch: pytest.MonkeyPatch) -> None:
    """If a future manifest's `title` already contains the legislation
    number (e.g. "5326 Sayılı Kabahatler Kanunu" as one field), the number
    must not be prepended a second time."""
    embed._load_manifest_entries.cache_clear()
    monkeypatch.setattr(
        embed.ingest,
        "SOURCE_MANIFEST_PATH",
        _write_manifest_fixture(
            [{"document_id": "doc_x", "legislation_number": "9999", "title": "9999 Sayılı Örnek Kanun"}]
        ),
    )
    try:
        title = embed.build_document_display_title("doc_x", "9999")
        assert title == "9999 Sayılı Örnek Kanun"
        assert title.count("9999") == 1
    finally:
        embed._load_manifest_entries.cache_clear()


def _write_manifest_fixture(entries: list[dict]) -> Path:
    import tempfile

    tmp_dir = Path(tempfile.mkdtemp())
    path = tmp_dir / "source_manifest.json"
    path.write_text(json.dumps(entries), encoding="utf-8")
    return path


def test_display_title_falls_back_without_inventing(monkeypatch: pytest.MonkeyPatch) -> None:
    embed._load_manifest_entries.cache_clear()
    monkeypatch.setattr(embed.ingest, "SOURCE_MANIFEST_PATH", _write_manifest_fixture([]))
    try:
        title = embed.build_document_display_title("unknown_doc", "1234")
        assert title == "1234"  # falls back to the real legislation number, never a guess
    finally:
        embed._load_manifest_entries.cache_clear()


# --- embed_texts: batching, ordering, usage ------------------------------------


def test_embed_texts_preserves_order_across_batches() -> None:
    texts = [f"text-{i}" for i in range(7)]
    client = _FakeClient(_default_responder())
    result = embed.embed_texts(texts, client=client, model="text-embedding-3-small", batch_size=3)

    assert len(result.vectors) == 7
    for i, text in enumerate(texts):
        assert result.vectors[i] == _deterministic_vector(text)
    assert len(client.embeddings.calls) == 3  # ceil(7/3)


def test_embed_texts_single_request_when_fewer_than_batch_size() -> None:
    texts = ["a", "b"]
    client = _FakeClient(_default_responder())
    embed.embed_texts(texts, client=client, model="text-embedding-3-small", batch_size=64)
    assert len(client.embeddings.calls) == 1


def test_embed_texts_batch_size_zero_raises() -> None:
    with pytest.raises(ValueError):
        embed.embed_texts(["a"], client=_FakeClient(_default_responder()), batch_size=0)


def test_embed_texts_negative_batch_size_raises() -> None:
    with pytest.raises(ValueError):
        embed.embed_texts(["a"], client=_FakeClient(_default_responder()), batch_size=-5)


def test_embed_texts_usage_aggregated_across_batches() -> None:
    texts = [f"t{i}" for i in range(5)]
    client = _FakeClient(_default_responder(prompt_tokens_per_input=10))
    result = embed.embed_texts(texts, client=client, model="text-embedding-3-small", batch_size=2)
    assert result.usage.prompt_tokens == 50
    assert result.usage.total_tokens == 50


def test_embed_texts_no_usage_reported_stays_none() -> None:
    """No batch (across multiple batches) reports usage -> both fields None,
    never 0."""

    def responder(model: str, texts: list[str]) -> _FakeResponse:
        data = [_FakeEmbeddingItem(index=i, embedding=_deterministic_vector(t)) for i, t in enumerate(texts)]
        return _FakeResponse(data=data, usage=None)

    client = _FakeClient(responder)
    result = embed.embed_texts([f"t{i}" for i in range(5)], client=client, model="m", batch_size=2)
    assert result.usage.prompt_tokens is None
    assert result.usage.total_tokens is None


def test_embed_texts_partial_batch_usage_reported_is_none_not_partial_sum() -> None:
    """One batch reports usage and another does not -> the aggregated field
    must be None, never a partial sum silently treated as the full total."""
    call_count = {"n": 0}

    def responder(model: str, texts: list[str]) -> _FakeResponse:
        call_count["n"] += 1
        data = [_FakeEmbeddingItem(index=i, embedding=_deterministic_vector(t)) for i, t in enumerate(texts)]
        if call_count["n"] == 1:
            usage = _FakeUsage(prompt_tokens=10, total_tokens=10)
        else:
            usage = None  # second batch reports nothing at all
        return _FakeResponse(data=data, usage=usage)

    client = _FakeClient(responder)
    result = embed.embed_texts([f"t{i}" for i in range(4)], client=client, model="m", batch_size=2)

    assert len(client.embeddings.calls) == 2  # sanity: two batches really happened
    assert result.usage.prompt_tokens is None
    assert result.usage.total_tokens is None


def test_embed_texts_per_field_usage_completeness_is_independent() -> None:
    """One individual usage field can be missing while the other is present
    on the same batch - each field's completeness is tracked on its own."""

    class _PartialUsage:
        def __init__(self, total_tokens: int) -> None:
            self.total_tokens = total_tokens
            # prompt_tokens intentionally absent (not even None as an attribute)

    def responder(model: str, texts: list[str]) -> _FakeResponse:
        data = [_FakeEmbeddingItem(index=i, embedding=_deterministic_vector(t)) for i, t in enumerate(texts)]
        return _FakeResponse(data=data, usage=_PartialUsage(total_tokens=25))

    client = _FakeClient(responder)
    result = embed.embed_texts(["a", "b"], client=client, model="m")

    assert result.usage.prompt_tokens is None  # never reported -> None
    assert result.usage.total_tokens == 25  # fully reported -> real aggregated total


def test_embed_texts_does_not_require_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "OPENAI_API_KEY", None)
    client = _FakeClient(_default_responder())
    result = embed.embed_texts(["a"], client=client, model="m")
    assert len(result.vectors) == 1


# --- embed_chunks: chunk_id mapping ---------------------------------------------


def test_embed_chunks_maps_vectors_to_correct_chunk_ids() -> None:
    chunks = [
        _c(chunk_id="c-1", text="first chunk text"),
        _c(chunk_id="c-2", text="second chunk text, a bit longer"),
        _c(chunk_id="c-3", text="third"),
    ]
    client = _FakeClient(_default_responder())
    run = embed.embed_chunks(chunks, client=client, model="text-embedding-3-small", batch_size=64)

    assert [r.chunk_id for r in run.results] == ["c-1", "c-2", "c-3"]
    for chunk, result in zip(chunks, run.results):
        expected_text = embed.build_embedding_text(chunk)
        assert result.embedding == _deterministic_vector(expected_text)
    assert run.input_count == 3
    assert run.vector_dimensionality == 4


def test_embed_chunks_include_embedding_text_flag() -> None:
    chunks = [_c(chunk_id="c-1")]
    client = _FakeClient(_default_responder())
    run = embed.embed_chunks(chunks, client=client, include_embedding_text=True)
    assert run.results[0].embedding_text == embed.build_embedding_text(chunks[0])

    run_default = embed.embed_chunks(chunks, client=_FakeClient(_default_responder()))
    assert run_default.results[0].embedding_text is None


def test_embed_chunks_batch_count_reported() -> None:
    chunks = [_c(chunk_id=f"c-{i}") for i in range(5)]
    client = _FakeClient(_default_responder())
    run = embed.embed_chunks(chunks, client=client, batch_size=2)
    assert run.batch_count == 3  # ceil(5/2)


def test_embed_chunks_batch_size_invalid_raises() -> None:
    with pytest.raises(ValueError):
        embed.embed_chunks([_c()], client=_FakeClient(_default_responder()), batch_size=0)


# --- Defensive response validation ----------------------------------------------


def test_response_count_mismatch_raises() -> None:
    def responder(model: str, texts: list[str]) -> _FakeResponse:
        data = [_FakeEmbeddingItem(index=0, embedding=_deterministic_vector(texts[0]))]
        return _FakeResponse(data=data, usage=None)  # missing one item vs 2 inputs

    client = _FakeClient(responder)
    with pytest.raises(embed.EmbeddingError):
        embed.embed_texts(["a", "b"], client=client, model="m")


def test_duplicate_response_index_raises() -> None:
    def responder(model: str, texts: list[str]) -> _FakeResponse:
        data = [
            _FakeEmbeddingItem(index=0, embedding=_deterministic_vector("x")),
            _FakeEmbeddingItem(index=0, embedding=_deterministic_vector("y")),
        ]
        return _FakeResponse(data=data, usage=None)

    client = _FakeClient(responder)
    with pytest.raises(embed.EmbeddingError):
        embed.embed_texts(["a", "b"], client=client, model="m")


def test_invalid_response_index_raises() -> None:
    def responder(model: str, texts: list[str]) -> _FakeResponse:
        data = [
            _FakeEmbeddingItem(index=0, embedding=_deterministic_vector("x")),
            _FakeEmbeddingItem(index=5, embedding=_deterministic_vector("y")),  # out of range for a batch of 2
        ]
        return _FakeResponse(data=data, usage=None)

    client = _FakeClient(responder)
    with pytest.raises(embed.EmbeddingError):
        embed.embed_texts(["a", "b"], client=client, model="m")


def test_empty_embedding_vector_raises() -> None:
    def responder(model: str, texts: list[str]) -> _FakeResponse:
        data = [_FakeEmbeddingItem(index=i, embedding=[]) for i in range(len(texts))]
        return _FakeResponse(data=data, usage=None)

    client = _FakeClient(responder)
    with pytest.raises(embed.EmbeddingError):
        embed.embed_texts(["a"], client=client, model="m")


def test_inconsistent_vector_dimensions_raises() -> None:
    call_count = {"n": 0}

    def responder(model: str, texts: list[str]) -> _FakeResponse:
        call_count["n"] += 1
        dim = 4 if call_count["n"] == 1 else 6
        data = [_FakeEmbeddingItem(index=i, embedding=[0.0] * dim) for i in range(len(texts))]
        return _FakeResponse(data=data, usage=None)

    client = _FakeClient(responder)
    with pytest.raises(embed.EmbeddingError):
        embed.embed_texts(["a", "b"], client=client, model="m", batch_size=1)


def test_non_numeric_vector_raises() -> None:
    def responder(model: str, texts: list[str]) -> _FakeResponse:
        data = [_FakeEmbeddingItem(index=0, embedding=["not", "numbers"])]
        return _FakeResponse(data=data, usage=None)

    client = _FakeClient(responder)
    with pytest.raises(embed.EmbeddingError):
        embed.embed_texts(["a"], client=client, model="m")


# ============================================================================
# Optional integration tests: real OpenAI API
# ============================================================================


@pytest.mark.integration
@pytest.mark.skipif(not _REAL_API_AVAILABLE, reason=_SKIP_REASON)
def test_integration_real_openai_small_sample_validation() -> None:
    """Small (1-3 Chunk) real-API validation. Never prints the API key or
    full vectors. See docs/indexing.md §9-§11."""
    chunks = [_c(chunk_id="c-1"), _c(chunk_id="c-2", article_no="3", text="Madde 3- (1) Kısa örnek.")]
    run = embed.embed_chunks(chunks, model=config.EMBEDDING_MODEL)

    assert run.input_count == len(chunks)
    assert [r.chunk_id for r in run.results] == ["c-1", "c-2"]
    dim = run.vector_dimensionality
    assert dim is not None and dim > 0
    assert all(len(r.embedding) == dim for r in run.results)


@pytest.mark.integration
@pytest.mark.skipif(not _REAL_API_AVAILABLE, reason=_SKIP_REASON)
@pytest.mark.skipif(
    not REAL_CHUNKS_PATH.exists(), reason=f"integration test: real chunks file not present locally: {REAL_CHUNKS_PATH}"
)
def test_integration_real_openai_all_53_chunks() -> None:
    """Full real-source validation: only runs after the small-sample test
    above has already validated authentication/model/response shape. Embeds
    all real 5326 Chunks and checks exact count/order alignment - never
    writes to Chroma, never prints vectors."""
    small_chunks = [_c(chunk_id="c-1")]
    embed.embed_chunks(small_chunks, model=config.EMBEDDING_MODEL)  # re-validated before the full run

    chunks = embed._load_chunks_from_json(REAL_CHUNKS_PATH)
    run = embed.embed_chunks(chunks, model=config.EMBEDDING_MODEL)

    assert len(chunks) == 53
    assert run.input_count == 53
    assert [r.chunk_id for r in run.results] == [c.chunk_id for c in chunks]
    assert run.vector_dimensionality is not None and run.vector_dimensionality > 0
