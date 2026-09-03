"""
Chroma vector persistence for validated Chunks + their precomputed
embeddings (Milestone M4B).

Scope: Chunk + EmbeddingResult -> Chroma PersistentClient upsert. This
module does NOT compute embeddings (see `src/embed.py`), does NOT implement
semantic retrieval/query embeddings (`src/retrieve.py`, a later milestone),
and does NOT call an LLM. See docs/indexing.md for the full contract this
module implements.

Module boundary: `src/chunk.py` (legal parsing/chunking) -> `src/embed.py`
(derived embedding text + OpenAI vectors) -> `src/index.py` (this module:
Chroma persistence) -> `src/retrieve.py` (future M5 retrieval). Chroma
persistence logic intentionally does not live in `src/embed.py`.

Chroma record contract (docs/indexing.md §4, §6):
  - id: `Chunk.chunk_id`
  - document: `Chunk.text`, unchanged - the canonical legal source text used
    later for grounding/citations. The derived `build_embedding_text()`
    representation from src/embed.py is only ever the text that was
    embedded; it is never stored as the Chroma document.
  - embedding: the corresponding precomputed vector from an
    `embed.EmbeddingRunResult` (never recomputed here).
  - metadata: see `build_chroma_metadata()`.

No automatic embedding function: collections are created/opened with
`embedding_function=None` (docs/indexing.md §3) since embeddings are always
supplied precomputed by `src/embed.py`.

Idempotency: indexing uses Chroma's `upsert()`, never `add()` - re-running
the same deterministic `chunk_id`s updates existing records in place rather
than creating duplicates (docs/indexing.md §8).

Security: never logs/prints secrets, full embedding vectors, or full legal
text (see `index_chunks`/CLI docstrings).

CLI usage (manual/local validation only - not part of the automated test
suite; requires BOTH `OPENAI_API_KEY` and `RUN_OPENAI_INTEGRATION_TESTS=1` to
embed, since indexing needs real vectors - the same explicit opt-in gate as
src/embed.py's real API tests, so a developer with a local .env key cannot
accidentally trigger a real OpenAI call just by running this CLI):
    RUN_OPENAI_INTEGRATION_TESTS=1 python -m src.index data/processed/5326-kabahatler-kanunu.chunks.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection

from src import config
from src.chunk import Chunk
from src.embed import EmbeddingResult

if __name__ == "__main__":  # pragma: no cover - exercised via CLI, not tests
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


class IndexingError(RuntimeError):
    """Raised when Chunks and embedding results cannot be safely aligned and
    written to Chroma - e.g. a count mismatch, duplicate/missing chunk_ids,
    an empty vector, or inconsistent vector dimensionality. Never silently
    associate a vector with the wrong Chunk; raise instead.
    """


# ============================================================================
# Typed summary
# ============================================================================


@dataclass(frozen=True)
class IndexingResult:
    """Operational summary of one `index_chunks()` run (docs/indexing.md
    §10). Never carries full vectors or full legal text."""

    collection_name: str
    submitted_count: int
    upserted_count: int
    collection_count: int
    batch_count: int
    vector_dimensionality: int | None
    persistence_path: str


# ============================================================================
# Chroma client/collection
# ============================================================================


def get_client(path: str | Path = config.CHROMA_PATH) -> chromadb.ClientAPI:
    """Open a local Chroma `PersistentClient` at `path`.

    `path` defaults to `src.config.CHROMA_PATH`; tests inject a `tmp_path`
    here so unit tests never write into the project's real `chroma/`
    directory (see docs/indexing.md §7).
    """
    return chromadb.PersistentClient(path=str(path))


def get_collection(
    client: chromadb.ClientAPI, name: str = config.COLLECTION_NAME
) -> Collection:
    """Get or create the Chroma collection named `name` (defaults to
    `src.config.COLLECTION_NAME` - never hard-coded here).

    Always created/opened with `embedding_function=None` (docs/indexing.md
    §3): embeddings are always supplied precomputed by `src/embed.py`, so
    Chroma's automatic embedding function is never used.
    """
    return client.get_or_create_collection(name=name, embedding_function=None)


# ============================================================================
# Metadata contract (docs/indexing.md §6)
# ============================================================================


def build_chroma_metadata(chunk: Chunk) -> dict[str, Any]:
    """Build the Chroma metadata dict for one Chunk, per docs/indexing.md §6.

    Only real Chunk fields are used - no legal metadata is invented. Scalar
    optional fields (`article_title`, `section_context`) are omitted
    entirely when `None` (never written as the literal string "None").
    `paragraph_numbers` (list[str]) and `footnote_references` (list[int])
    are written as native, homogeneous Chroma arrays - never comma-joined
    strings, since the pinned Chroma version (see requirements.txt) verified
    native array metadata support (see module docstring / the M4B smoke
    test) - and are omitted entirely when `None` or empty (Chroma does not
    allow empty arrays).
    """
    metadata: dict[str, Any] = {
        "article_id": chunk.article_id,
        "document_id": chunk.document_id,
        "legislation_number": chunk.legislation_number,
        "article_no": chunk.article_no,
        "article_type": chunk.article_type,
        "source_paragraph_start": chunk.source_paragraph_start,
        "source_paragraph_end": chunk.source_paragraph_end,
    }
    # Required-on-Chunk fields above are never None; document_id/
    # legislation_number are typed optional on Chunk but still omitted here
    # if actually None, for consistency with the other optional fields.
    metadata = {k: v for k, v in metadata.items() if v is not None}

    if chunk.article_title:
        metadata["article_title"] = chunk.article_title
    if chunk.section_context:
        metadata["section_context"] = chunk.section_context
    if chunk.paragraph_numbers:
        metadata["paragraph_numbers"] = list(chunk.paragraph_numbers)
    if chunk.footnote_references:
        metadata["footnote_references"] = list(chunk.footnote_references)

    return metadata


# ============================================================================
# Alignment validation (docs/indexing.md §7)
# ============================================================================


def _validate_batch_size(batch_size: int) -> None:
    if batch_size <= 0:
        raise IndexingError(f"batch_size must be > 0, got {batch_size}")


def _validate_alignment(chunks: list[Chunk], results: list[EmbeddingResult]) -> dict[str, EmbeddingResult]:
    """Validate that `chunks` and `results` describe an exact, unambiguous
    chunk_id <-> embedding relationship before anything is written to
    Chroma. Returns a `chunk_id -> EmbeddingResult` map so callers can write
    in Chunk source order regardless of the order `results` arrived in.

    Rejects (raises `IndexingError`, never silently continues):
      - Chunk count != embedding result count
      - duplicate chunk_ids among `chunks`
      - duplicate chunk_ids among `results`
      - any Chunk with no matching embedding result (missing)
      - any embedding result with no matching Chunk (extra)
      - an empty vector
      - inconsistent vector dimensionality across results
    """
    if len(chunks) != len(results):
        raise IndexingError(
            f"Chunk count ({len(chunks)}) does not match embedding result count ({len(results)})"
        )

    chunk_ids = [c.chunk_id for c in chunks]
    if len(set(chunk_ids)) != len(chunk_ids):
        duplicates = sorted({cid for cid in chunk_ids if chunk_ids.count(cid) > 1})
        raise IndexingError(f"Duplicate Chunk IDs: {duplicates}")

    result_ids = [r.chunk_id for r in results]
    if len(set(result_ids)) != len(result_ids):
        duplicates = sorted({rid for rid in result_ids if result_ids.count(rid) > 1})
        raise IndexingError(f"Duplicate embedding result chunk_ids: {duplicates}")

    chunk_id_set = set(chunk_ids)
    result_id_set = set(result_ids)
    missing = chunk_id_set - result_id_set
    if missing:
        raise IndexingError(f"Chunks with no matching embedding result: {sorted(missing)}")
    extra = result_id_set - chunk_id_set
    if extra:
        raise IndexingError(f"Embedding results with no matching Chunk: {sorted(extra)}")

    dimensionality: int | None = None
    for result in results:
        vector = result.embedding
        if not isinstance(vector, (list, tuple)) or len(vector) == 0:
            raise IndexingError(f"Empty or invalid embedding vector for chunk_id {result.chunk_id!r}")
        if dimensionality is None:
            dimensionality = len(vector)
        elif len(vector) != dimensionality:
            raise IndexingError(
                f"Inconsistent embedding dimensionality: expected {dimensionality}, "
                f"got {len(vector)} for chunk_id {result.chunk_id!r}"
            )

    return {r.chunk_id: r for r in results}


# ============================================================================
# Indexing (docs/indexing.md §8-§9)
# ============================================================================


def index_chunks(
    chunks: list[Chunk],
    results: list[EmbeddingResult],
    *,
    collection: Collection,
    batch_size: int = 64,
) -> IndexingResult:
    """Upsert `chunks` (with their precomputed `results` embeddings) into a
    Chroma `collection`, in Chunk source order.

    Validates exact chunk_id <-> embedding alignment first (see
    `_validate_alignment`) - vectors are mapped to Chunks by `chunk_id`, not
    by list position, so a `results` list in a different order than `chunks`
    is still written correctly as long as every chunk_id matches exactly;
    any mismatch raises `IndexingError` rather than silently pairing the
    wrong vector with a Chunk.

    Idempotent: uses `collection.upsert()`, never `add()` - re-running this
    with the same `chunk_id`s updates the existing records (document,
    embedding, metadata) in place rather than creating duplicates.

    Writes in batches of `batch_size` (must be > 0) rather than one giant
    call, so a larger future corpus does not require one unbounded upsert.
    """
    _validate_batch_size(batch_size)
    results_by_id = _validate_alignment(chunks, results)

    vector_dimensionality = len(results[0].embedding) if results else None
    batch_count = 0

    for batch_start in range(0, len(chunks), batch_size):
        batch_chunks = chunks[batch_start : batch_start + batch_size]
        batch_count += 1

        ids = [c.chunk_id for c in batch_chunks]
        documents = [c.text for c in batch_chunks]
        embeddings = [results_by_id[c.chunk_id].embedding for c in batch_chunks]
        metadatas = [build_chroma_metadata(c) for c in batch_chunks]

        collection.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)

    return IndexingResult(
        collection_name=collection.name,
        submitted_count=len(chunks),
        upserted_count=len(chunks),
        collection_count=collection.count(),
        batch_count=batch_count,
        vector_dimensionality=vector_dimensionality,
        persistence_path=str(config.CHROMA_PATH),
    )


# ============================================================================
# CLI (manual/local validation only - see docs/indexing.md §12-§13)
# ============================================================================


def _load_chunks_from_json(chunks_json_path: Path) -> list[Chunk]:
    data = json.loads(chunks_json_path.read_text(encoding="utf-8"))
    return [Chunk(**c) for c in data["chunks"]]


def _real_indexing_opt_in() -> bool:
    """Explicit opt-in gate for real OpenAI + Chroma indexing, mirroring the
    gate already established for M4A's real API tests (see
    tests/test_embed.py): a real embedding call is only ever made when BOTH
    `config.OPENAI_API_KEY` is available AND `RUN_OPENAI_INTEGRATION_TESTS=1`
    is set. Neither one alone is enough - a developer with a local .env key
    must not be able to trigger a real, billed OpenAI call just by running
    this CLI without also opting in explicitly.
    """
    return bool(config.OPENAI_API_KEY) and os.getenv("RUN_OPENAI_INTEGRATION_TESTS") == "1"


def main(argv: list[str] | None = None) -> None:
    """Manual/local end-to-end indexing CLI - NOT part of the automated test
    suite. Embeds real Chunks and upserts them into the local Chroma
    `PersistentClient`, but only when explicit opt-in is enabled (see
    `_real_indexing_opt_in`): both `OPENAI_API_KEY` and
    `RUN_OPENAI_INTEGRATION_TESTS=1` must be set, otherwise this exits
    cleanly before loading the corpus, embedding, or touching Chroma. Prints
    an operational summary only: never the API key, never full embedding
    vectors, never full legal text.
    """
    parser = argparse.ArgumentParser(
        description="Embed and index Chunks from a *.chunks.json file into local Chroma."
    )
    parser.add_argument("chunks_json", type=Path, help="Path to a *.chunks.json produced by src.chunk")
    parser.add_argument("--batch-size", type=int, default=64, help="Upsert batch size (default: 64)")
    parser.add_argument(
        "--sample-size", type=int, default=None, help="Index only the first N Chunks (quick validation run)"
    )
    args = parser.parse_args(argv)

    if not _real_indexing_opt_in():
        print(
            "Real indexing skipped: requires both OPENAI_API_KEY and "
            "RUN_OPENAI_INTEGRATION_TESTS=1 (explicit opt-in not enabled or "
            "credentials unavailable)."
        )
        return

    from src import embed  # local import: keeps `src.embed` optional for pure-indexing use

    chunks = _load_chunks_from_json(args.chunks_json)
    if args.sample_size is not None:
        chunks = chunks[: args.sample_size]

    run = embed.embed_chunks(chunks, batch_size=args.batch_size)

    client = get_client()
    collection = get_collection(client)
    result = index_chunks(chunks, run.results, collection=collection, batch_size=args.batch_size)

    print(f"Input file: {args.chunks_json}")
    print(f"Collection: {result.collection_name}")
    print(f"Persistence path: {result.persistence_path}")
    print(f"Submitted Chunk count: {result.submitted_count}")
    print(f"Upserted count: {result.upserted_count}")
    print(f"Collection count: {result.collection_count}")
    print(f"Batch count: {result.batch_count}")
    print(f"Vector dimensionality: {result.vector_dimensionality}")


if __name__ == "__main__":
    main()
