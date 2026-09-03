"""Tests for src/index.py (M4B Chroma vector indexing).

All tests use a local, temporary Chroma `PersistentClient` rooted at
pytest's `tmp_path` (never the project's real `chroma/` directory), and
small deterministic fake vectors built directly as `embed.EmbeddingResult`
objects - they never call OpenAI, never require `OPENAI_API_KEY`, and never
use any network service. Every upsert in this file supplies embeddings
explicitly, so Chroma's fallback default embedding function (triggered only
when embeddings are omitted from add()/upsert() - see module notes) is never
exercised here.

A separate, clearly-named integration section is intentionally NOT in this
file - the real end-to-end OpenAI-embed + Chroma-index validation is a
manual CLI run (`python -m src.index ...`), gated the same way as
src/embed.py's real API tests (`OPENAI_API_KEY` + `RUN_OPENAI_INTEGRATION_TESTS=1`).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src import config, index
from src.chunk import Chunk
from src.embed import EmbeddingResult

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


def _r(chunk_id: str, embedding: list[float] | None = None, model: str = "fake-model") -> EmbeddingResult:
    return EmbeddingResult(
        chunk_id=chunk_id, embedding=[1.0, 2.0, 3.0, 4.0] if embedding is None else embedding, model=model
    )


def _fresh_collection(tmp_path: Path, name: str = "test-collection"):
    client = index.get_client(tmp_path)
    collection = index.get_collection(client, name)
    return client, collection


# ============================================================================
# 1-6: build_chroma_metadata
# ============================================================================


def test_build_chroma_metadata_preserves_scalar_fields() -> None:
    chunk = _c(article_no="2", article_type="normal", section_context="Birinci Kısım > Birinci Bölüm")
    meta = index.build_chroma_metadata(chunk)
    assert meta["article_id"] == chunk.article_id
    assert meta["document_id"] == "5326_kabahatler_kanunu"
    assert meta["legislation_number"] == "5326"
    assert meta["article_no"] == "2"
    assert meta["article_type"] == "normal"
    assert meta["article_title"] == "Tanım"
    assert meta["section_context"] == "Birinci Kısım > Birinci Bölüm"
    assert meta["source_paragraph_start"] == 22
    assert meta["source_paragraph_end"] == 22


def test_build_chroma_metadata_paragraph_numbers_native_string_array() -> None:
    chunk = _c(paragraph_numbers=["1", "2"])
    meta = index.build_chroma_metadata(chunk)
    assert meta["paragraph_numbers"] == ["1", "2"]
    assert all(isinstance(n, str) for n in meta["paragraph_numbers"])


def test_build_chroma_metadata_footnote_references_native_int_array() -> None:
    chunk = _c(footnote_references=[3, 7])
    meta = index.build_chroma_metadata(chunk)
    assert meta["footnote_references"] == [3, 7]
    assert all(isinstance(n, int) for n in meta["footnote_references"])


def test_build_chroma_metadata_omits_none_optional_scalars() -> None:
    chunk = _c(article_title=None, section_context=None)
    meta = index.build_chroma_metadata(chunk)
    assert "article_title" not in meta
    assert "section_context" not in meta


def test_build_chroma_metadata_omits_empty_arrays() -> None:
    chunk = _c(paragraph_numbers=[], footnote_references=[])
    meta = index.build_chroma_metadata(chunk)
    assert "paragraph_numbers" not in meta
    assert "footnote_references" not in meta


def test_build_chroma_metadata_never_writes_literal_none_string() -> None:
    chunk = _c(article_title=None, section_context=None, paragraph_numbers=None, footnote_references=None)
    meta = index.build_chroma_metadata(chunk)
    for value in meta.values():
        assert value != "None"
        if isinstance(value, list):
            assert "None" not in value


# ============================================================================
# 7-9: Chroma record contract (id / document / embedding)
# ============================================================================


def test_chroma_document_equals_chunk_text_exactly(tmp_path: Path) -> None:
    chunk = _c(text="Madde 2- (1) Kabahat deyiminden idarî yaptırım anlaşılır.")
    _, collection = _fresh_collection(tmp_path)
    index.index_chunks([chunk], [_r(chunk.chunk_id)], collection=collection)

    got = collection.get(ids=[chunk.chunk_id], include=["documents"])
    assert got["documents"][0] == chunk.text


def test_chroma_id_equals_chunk_id(tmp_path: Path) -> None:
    chunk = _c(chunk_id="5326-madde-9-chunk-001")
    _, collection = _fresh_collection(tmp_path)
    index.index_chunks([chunk], [_r(chunk.chunk_id)], collection=collection)

    got = collection.get(ids=[chunk.chunk_id])
    assert got["ids"] == ["5326-madde-9-chunk-001"]


def test_precomputed_vector_is_stored(tmp_path: Path) -> None:
    chunk = _c()
    vector = [0.5, 1.5, 2.5, 3.5]
    _, collection = _fresh_collection(tmp_path)
    index.index_chunks([chunk], [_r(chunk.chunk_id, embedding=vector)], collection=collection)

    got = collection.get(ids=[chunk.chunk_id], include=["embeddings"])
    assert list(got["embeddings"][0]) == vector


# ============================================================================
# 10-13: native array round-trip + $contains filtering
# ============================================================================


def test_native_string_array_metadata_round_trips(tmp_path: Path) -> None:
    chunk = _c(paragraph_numbers=["1", "2", "3"])
    _, collection = _fresh_collection(tmp_path)
    index.index_chunks([chunk], [_r(chunk.chunk_id)], collection=collection)

    got = collection.get(ids=[chunk.chunk_id], include=["metadatas"])
    assert got["metadatas"][0]["paragraph_numbers"] == ["1", "2", "3"]


def test_native_int_array_metadata_round_trips(tmp_path: Path) -> None:
    chunk = _c(footnote_references=[4, 9])
    _, collection = _fresh_collection(tmp_path)
    index.index_chunks([chunk], [_r(chunk.chunk_id)], collection=collection)

    got = collection.get(ids=[chunk.chunk_id], include=["metadatas"])
    assert got["metadatas"][0]["footnote_references"] == [4, 9]


def test_contains_filter_works_for_paragraph_numbers(tmp_path: Path) -> None:
    chunk_a = _c(chunk_id="c-a", paragraph_numbers=["1", "2"])
    chunk_b = _c(chunk_id="c-b", article_no="3", paragraph_numbers=["5"])
    _, collection = _fresh_collection(tmp_path)
    index.index_chunks(
        [chunk_a, chunk_b], [_r("c-a"), _r("c-b")], collection=collection
    )

    filtered = collection.get(where={"paragraph_numbers": {"$contains": "2"}})
    assert filtered["ids"] == ["c-a"]


def test_contains_filter_works_for_footnote_references(tmp_path: Path) -> None:
    chunk_a = _c(chunk_id="c-a", footnote_references=[3, 7])
    chunk_b = _c(chunk_id="c-b", article_no="3", footnote_references=[9])
    _, collection = _fresh_collection(tmp_path)
    index.index_chunks(
        [chunk_a, chunk_b], [_r("c-a"), _r("c-b")], collection=collection
    )

    filtered = collection.get(where={"footnote_references": {"$contains": 7}})
    assert filtered["ids"] == ["c-a"]


# ============================================================================
# 14-20: alignment validation / defensive errors
# ============================================================================


def test_mismatched_chunk_embedding_count_raises(tmp_path: Path) -> None:
    _, collection = _fresh_collection(tmp_path)
    with pytest.raises(index.IndexingError):
        index.index_chunks([_c(chunk_id="c-1"), _c(chunk_id="c-2")], [_r("c-1")], collection=collection)


def test_missing_chunk_id_mapping_raises(tmp_path: Path) -> None:
    """One Chunk has no matching embedding result chunk_id."""
    _, collection = _fresh_collection(tmp_path)
    chunks = [_c(chunk_id="c-1"), _c(chunk_id="c-2")]
    results = [_r("c-1"), _r("c-3")]  # c-2 missing, c-3 is extra
    with pytest.raises(index.IndexingError):
        index.index_chunks(chunks, results, collection=collection)


def test_duplicate_chunk_ids_raise(tmp_path: Path) -> None:
    _, collection = _fresh_collection(tmp_path)
    chunks = [_c(chunk_id="c-1"), _c(chunk_id="c-1")]
    results = [_r("c-1"), _r("c-1")]
    with pytest.raises(index.IndexingError):
        index.index_chunks(chunks, results, collection=collection)


def test_duplicate_embedding_result_ids_raise(tmp_path: Path) -> None:
    _, collection = _fresh_collection(tmp_path)
    chunks = [_c(chunk_id="c-1"), _c(chunk_id="c-2")]
    results = [_r("c-1"), _r("c-1")]  # duplicate result id, c-2 never supplied
    with pytest.raises(index.IndexingError):
        index.index_chunks(chunks, results, collection=collection)


def test_empty_vector_raises(tmp_path: Path) -> None:
    _, collection = _fresh_collection(tmp_path)
    chunk = _c(chunk_id="c-1")
    with pytest.raises(index.IndexingError):
        index.index_chunks([chunk], [_r("c-1", embedding=[])], collection=collection)


def test_inconsistent_vector_dimensions_raise(tmp_path: Path) -> None:
    _, collection = _fresh_collection(tmp_path)
    chunks = [_c(chunk_id="c-1"), _c(chunk_id="c-2")]
    results = [_r("c-1", embedding=[1.0, 2.0]), _r("c-2", embedding=[1.0, 2.0, 3.0])]
    with pytest.raises(index.IndexingError):
        index.index_chunks(chunks, results, collection=collection)


def test_batch_size_zero_or_negative_raises(tmp_path: Path) -> None:
    _, collection = _fresh_collection(tmp_path)
    chunk = _c(chunk_id="c-1")
    with pytest.raises(index.IndexingError):
        index.index_chunks([chunk], [_r("c-1")], collection=collection, batch_size=0)
    with pytest.raises(index.IndexingError):
        index.index_chunks([chunk], [_r("c-1")], collection=collection, batch_size=-1)


# ============================================================================
# 21-24: idempotency, upsert semantics, persistence
# ============================================================================


def test_first_upsert_writes_n_records(tmp_path: Path) -> None:
    chunks = [_c(chunk_id=f"c-{i}", article_no=str(i)) for i in range(5)]
    results = [_r(c.chunk_id) for c in chunks]
    _, collection = _fresh_collection(tmp_path)

    result = index.index_chunks(chunks, results, collection=collection)
    assert result.collection_count == 5
    assert result.submitted_count == 5
    assert result.upserted_count == 5


def test_second_identical_upsert_keeps_collection_count(tmp_path: Path) -> None:
    chunks = [_c(chunk_id=f"c-{i}", article_no=str(i)) for i in range(5)]
    results = [_r(c.chunk_id) for c in chunks]
    _, collection = _fresh_collection(tmp_path)

    index.index_chunks(chunks, results, collection=collection)
    second = index.index_chunks(chunks, results, collection=collection)
    assert second.collection_count == 5  # NOT 10


def test_same_id_updated_without_increasing_count(tmp_path: Path) -> None:
    chunk = _c(chunk_id="c-1", text="original text")
    _, collection = _fresh_collection(tmp_path)
    index.index_chunks([chunk], [_r("c-1", embedding=[1.0, 1.0, 1.0, 1.0])], collection=collection)

    updated_chunk = _c(chunk_id="c-1", text="updated text")
    result = index.index_chunks([updated_chunk], [_r("c-1", embedding=[9.0, 9.0, 9.0, 9.0])], collection=collection)

    assert result.collection_count == 1
    got = collection.get(ids=["c-1"], include=["documents", "embeddings"])
    assert got["documents"][0] == "updated text"
    assert list(got["embeddings"][0]) == [9.0, 9.0, 9.0, 9.0]


def test_persistence_survives_reopening_client(tmp_path: Path) -> None:
    chunks = [_c(chunk_id=f"c-{i}", article_no=str(i)) for i in range(3)]
    results = [_r(c.chunk_id) for c in chunks]

    client1 = index.get_client(tmp_path)
    collection1 = index.get_collection(client1, "test-collection")
    index.index_chunks(chunks, results, collection=collection1)
    del client1, collection1

    client2 = index.get_client(tmp_path)
    collection2 = index.get_collection(client2, "test-collection")
    assert collection2.count() == 3
    got = collection2.get(ids=["c-0"])
    assert got["ids"] == ["c-0"]


# ============================================================================
# 25: no automatic embedding function
# ============================================================================


def test_collection_has_no_automatic_embedding_function(tmp_path: Path) -> None:
    _, collection = _fresh_collection(tmp_path)
    assert collection._embedding_function is None


def test_indexing_stores_exactly_the_supplied_vector_not_a_computed_one(tmp_path: Path) -> None:
    """Proves indexing works entirely from supplied vectors: the stored
    embedding is exactly our arbitrary fake vector, never something a real
    (auto) embedding function would have computed from the document text."""
    chunk = _c(text="Bu metin hiçbir embedding modeline gönderilmedi.")
    distinctive_vector = [42.0, -7.5, 0.25, 1000.0]
    _, collection = _fresh_collection(tmp_path)
    index.index_chunks([chunk], [_r(chunk.chunk_id, embedding=distinctive_vector)], collection=collection)

    got = collection.get(ids=[chunk.chunk_id], include=["embeddings"])
    # Chroma stores embeddings as float32 internally; compare with tolerance
    # rather than requiring bit-exact float64 equality.
    assert list(got["embeddings"][0]) == pytest.approx(distinctive_vector)


# ============================================================================
# Misc: config wiring
# ============================================================================


def test_get_collection_uses_config_collection_name_by_default(tmp_path: Path) -> None:
    client = index.get_client(tmp_path)
    collection = index.get_collection(client)
    assert collection.name == config.COLLECTION_NAME


# ============================================================================
# 26-29: explicit opt-in gate for the real indexing CLI (main())
#
# Mirrors the gate already established for M4A's real API tests (see
# tests/test_embed.py): the real `main()` CLI must only ever reach
# `embed.embed_chunks()` (a real, billed OpenAI call) when BOTH
# `OPENAI_API_KEY` and `RUN_OPENAI_INTEGRATION_TESTS=1` are set. These tests
# never call OpenAI themselves - `embed.embed_chunks` and
# `index._load_chunks_from_json` are monkeypatched to functions that raise if
# invoked at all, so a call proves the gate leaked. None of these require the
# real corpus file or the project's real chroma/ directory.
# ============================================================================


def _forbidden_load_chunks(_path: Path) -> list[Chunk]:
    raise AssertionError("real corpus must not be loaded while the explicit opt-in gate is closed")


def _forbidden_embed_chunks(*_args, **_kwargs):
    raise AssertionError("embed.embed_chunks() must not be called while the explicit opt-in gate is closed")


def _assert_gate_closed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> str:
    import src.embed as embed_module

    monkeypatch.setattr(index, "_load_chunks_from_json", _forbidden_load_chunks)
    monkeypatch.setattr(embed_module, "embed_chunks", _forbidden_embed_chunks)

    index.main([str(tmp_path / "irrelevant.chunks.json")])

    return capsys.readouterr().out


def test_main_skips_when_key_present_but_flag_absent(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(config, "OPENAI_API_KEY", "sk-fake-key-not-real")
    monkeypatch.delenv("RUN_OPENAI_INTEGRATION_TESTS", raising=False)

    out = _assert_gate_closed(monkeypatch, tmp_path, capsys)
    assert "skip" in out.lower()
    assert "sk-fake-key-not-real" not in out


def test_main_skips_when_key_present_but_flag_not_exactly_one(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(config, "OPENAI_API_KEY", "sk-fake-key-not-real")
    monkeypatch.setenv("RUN_OPENAI_INTEGRATION_TESTS", "0")

    out = _assert_gate_closed(monkeypatch, tmp_path, capsys)
    assert "skip" in out.lower()
    assert "sk-fake-key-not-real" not in out


def test_main_skips_when_flag_set_but_key_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(config, "OPENAI_API_KEY", None)
    monkeypatch.setenv("RUN_OPENAI_INTEGRATION_TESTS", "1")

    out = _assert_gate_closed(monkeypatch, tmp_path, capsys)
    assert "skip" in out.lower()


def test_main_allows_real_operation_path_when_key_and_flag_both_set(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Both conditions met -> the CLI proceeds past the gate. `embed_chunks`
    is still faked here (this file never calls OpenAI even in the
    "allowed" case) - this only proves the gate itself opens, not that a
    real embedding happened."""
    from src.embed import EmbeddingRunResult, EmbeddingUsage
    import src.embed as embed_module

    monkeypatch.setattr(config, "OPENAI_API_KEY", "sk-fake-key-not-real")
    monkeypatch.setenv("RUN_OPENAI_INTEGRATION_TESTS", "1")

    # `index.get_client`'s default path argument is bound to `config.CHROMA_PATH`
    # at import time, so monkeypatching `config.CHROMA_PATH` alone would not
    # redirect it - `get_client` itself is wrapped to force a `tmp_path`
    # destination instead, so this test never touches the real chroma/ dir.
    real_get_client = index.get_client
    monkeypatch.setattr(index, "get_client", lambda *_a, **_k: real_get_client(tmp_path / "chroma"))

    chunks = [_c(chunk_id="c-1"), _c(chunk_id="c-2", article_no="3")]
    monkeypatch.setattr(index, "_load_chunks_from_json", lambda _path: chunks)

    calls: list[int] = []

    def fake_embed_chunks(passed_chunks: list[Chunk], *, batch_size: int = 64) -> EmbeddingRunResult:
        calls.append(len(passed_chunks))
        return EmbeddingRunResult(
            results=[_r(c.chunk_id) for c in passed_chunks],
            model="fake-model",
            batch_count=1,
            usage=EmbeddingUsage(),
        )

    monkeypatch.setattr(embed_module, "embed_chunks", fake_embed_chunks)

    index.main([str(tmp_path / "input.chunks.json")])

    assert calls == [2]  # the real-operation path was reached exactly once
    out = capsys.readouterr().out
    assert "sk-fake-key-not-real" not in out
    assert "Upserted count: 2" in out
