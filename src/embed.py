"""
OpenAI embedding service for validated Chunks (Milestone M4A).

Scope: Chunk -> derived embedding text -> OpenAI embedding vector. This
module does NOT write to Chroma, does NOT implement retrieval, and does NOT
alter `Chunk.text` (see docs/indexing.md for the full embedding/indexing
contract). Chroma indexing is a later milestone (see `docs/indexing.md`
§3-§8) and is intentionally not implemented here.

Embedding text vs. source text (docs/indexing.md §2): `Chunk.text` is the
immutable legal source text and remains the canonical text for citations and
answer grounding. This module builds a *separate*, derived "embedding text"
representation (document display title + article label + article title +
blank line + the unmodified Chunk.text) that is only ever used as the input
string sent to the embedding API - it is never substituted for Chunk.text,
never shown to a user as a legal quotation, and never written back onto the
Chunk domain model.

Security: the OpenAI API key is read only from `src.config.OPENAI_API_KEY`
(itself sourced from the environment/.env via the single centralized
`load_dotenv()` call in src/config.py - see that module; no other module,
including this one, calls `load_dotenv()` itself). This module never prints,
logs, or otherwise serializes the API key, and never prints full embedding
vectors or full legal document text.

CLI usage (manual/local validation only - not part of the automated test
suite):
    python -m src.embed data/processed/5326-kabahatler-kanunu.chunks.json
    python -m src.embed data/processed/5326-kabahatler-kanunu.chunks.json --sample-size 3
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from openai import OpenAI

from src import config, ingest
from src.chunk import Chunk

if __name__ == "__main__":  # pragma: no cover - exercised via CLI, not tests
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


class EmbeddingError(RuntimeError):
    """Raised when an embedding API response cannot be safely mapped back to
    the Chunks/texts that were submitted (see `_validate_batch_response`) -
    e.g. a count mismatch, a missing/duplicate/out-of-range response index,
    an empty vector, or inconsistent vector dimensionality across a run.
    Never silently continue with misaligned embeddings; raise instead.
    """


# ============================================================================
# Typed results
# ============================================================================


@dataclass(frozen=True)
class EmbeddingUsage:
    """Aggregated token usage across one or more embedding API calls.

    `prompt_tokens` and `total_tokens` are each completed independently: a
    field is only the real aggregated total if *every* aggregated call
    reported that field. If even one call did not report it, that field is
    `None` - never a partial sum silently treated as complete, and never `0`
    as a stand-in for "unknown". One field can be a real total while the
    other is `None` (e.g. if only `total_tokens` was omitted somewhere).
    """

    prompt_tokens: int | None = None
    total_tokens: int | None = None


@dataclass(frozen=True)
class TextEmbeddingBatch:
    """Result of embedding a flat list of input strings (see `embed_texts`).

    `vectors` is aligned 1:1 with the submitted `texts`, in the same order -
    index i of `vectors` is the embedding for `texts[i]`.
    """

    vectors: list[list[float]]
    model: str
    usage: EmbeddingUsage


@dataclass(frozen=True)
class EmbeddingResult:
    """One Chunk's embedding vector (see `embed_chunks`).

    `embedding_text` is included only when explicitly requested
    (`include_embedding_text=True`) and is kept strictly for
    debugging/testing - it is derived retrieval-context data, not canonical
    legal source text (see module docstring and docs/indexing.md §2). It is
    never written onto the Chunk domain model.
    """

    chunk_id: str
    embedding: list[float]
    model: str
    embedding_text: str | None = None


@dataclass(frozen=True)
class EmbeddingRunResult:
    """Summary of one `embed_chunks()` run: per-Chunk results plus
    operational reporting fields (see docs/indexing.md §11 cost note)."""

    results: list[EmbeddingResult]
    model: str
    batch_count: int
    usage: EmbeddingUsage

    @property
    def input_count(self) -> int:
        return len(self.results)

    @property
    def vector_dimensionality(self) -> int | None:
        return len(self.results[0].embedding) if self.results else None


# ============================================================================
# Embedding text construction (docs/indexing.md §2)
# ============================================================================

_ARTICLE_LABEL_PREFIXES = {"normal": "Madde", "ek": "Ek Madde", "gecici": "Geçici Madde"}


@lru_cache(maxsize=1)
def _load_manifest_entries() -> tuple[dict[str, Any], ...]:
    """Load data/source_manifest.json entries.

    Reuses `src.ingest`'s existing manifest path constant
    (`ingest.SOURCE_MANIFEST_PATH`) rather than hard-coding the path again;
    returns an empty tuple if the manifest is missing. Cached since the
    manifest is small, static per process, and looked up once per Chunk.
    """
    path = ingest.SOURCE_MANIFEST_PATH
    if not path.exists():
        return ()
    return tuple(json.loads(path.read_text(encoding="utf-8")))


def _find_manifest_entry(document_id: str | None, legislation_number: str | None) -> dict[str, Any]:
    """Find this document's data/source_manifest.json entry.

    Matches by `document_id` first (the more specific key), falling back to
    `legislation_number`. Returns `{}` if no entry matches - callers must not
    invent metadata for a missing entry (see `build_document_display_title`).
    """
    entries = _load_manifest_entries()
    if document_id:
        for entry in entries:
            if entry.get("document_id") == document_id:
                return entry
    if legislation_number:
        for entry in entries:
            if entry.get("legislation_number") == legislation_number:
                return entry
    return {}


def build_document_display_title(document_id: str | None, legislation_number: str | None) -> str:
    """Human-readable document title line for the embedding text header.

    Looked up from data/source_manifest.json (via `document_id`, falling
    back to `legislation_number`) rather than hard-coded, so additional
    legislation documents are supported without changing this function. If
    the manifest's `title` already contains the legislation number, the
    number is not prepended a second time (supports a future manifest entry
    whose `title` is already self-describing, e.g. "5326 Sayılı Kabahatler
    Kanunu" as a single field).

    Never invents a title: falls back to whatever real identifier is
    available (legislation_number, then document_id) if the manifest has no
    matching entry or no `title`, and returns "" only if nothing at all is
    available.
    """
    entry = _find_manifest_entry(document_id, legislation_number)
    title = entry.get("title")
    number = entry.get("legislation_number") or legislation_number

    if title and number and str(number) not in title:
        return f"{number} Sayılı {title}"
    if title:
        return title
    if number:
        return str(number)
    return document_id or ""


def build_article_label(article_type: str, article_no: str) -> str:
    """Article label line, e.g. "Madde 2", "Madde 42/A", "Ek Madde 1",
    "Geçici Madde 1" - matching how these headings appear in the real source
    (see docs/source-analysis-5326.md). Raises ValueError for an unrecognized
    `article_type` rather than guessing a label.
    """
    try:
        prefix = _ARTICLE_LABEL_PREFIXES[article_type]
    except KeyError:
        raise ValueError(f"Unknown article_type: {article_type!r}") from None
    return f"{prefix} {article_no}"


def build_embedding_text(chunk: Chunk) -> str:
    """Build the derived embedding-text representation for one Chunk, per
    docs/indexing.md §2:

        {document display title}
        {article label}
        {article title, only if present}

        {original Chunk.text, unmodified}

    This is retrieval-context data only, never a legal citation - it exists
    solely to improve embedding/retrieval quality. `chunk.text` itself is
    never rewritten, truncated, or normalized here.
    """
    display_title = build_document_display_title(chunk.document_id, chunk.legislation_number)
    article_label = build_article_label(chunk.article_type, chunk.article_no)

    header_lines = [display_title, article_label]
    if chunk.article_title:
        header_lines.append(chunk.article_title)

    return "\n".join(header_lines) + "\n\n" + chunk.text


# ============================================================================
# OpenAI embedding calls
# ============================================================================


def _validate_batch_size(batch_size: int) -> None:
    if batch_size <= 0:
        raise ValueError(f"batch_size must be > 0, got {batch_size}")


def _get_client() -> OpenAI:
    """Construct an OpenAI client from `src.config.OPENAI_API_KEY`.

    Only called when no `client` is explicitly passed in (see `embed_texts`/
    `embed_chunks`) - unit tests inject a fake client and never reach this
    function, so they never require a real API key. Never logs/prints the
    key.
    """
    if not config.OPENAI_API_KEY:
        raise EmbeddingError(
            "OPENAI_API_KEY is not configured. Set it in the environment/.env "
            "(see src/config.py) before requesting real embeddings."
        )
    return OpenAI(api_key=config.OPENAI_API_KEY)


def _validate_vector(vector: Any, *, index: int) -> None:
    if not isinstance(vector, (list, tuple)) or len(vector) == 0:
        raise EmbeddingError(f"Empty or invalid embedding vector at index {index}")
    if not all(isinstance(v, (int, float)) for v in vector):
        raise EmbeddingError(f"Non-numeric embedding vector at index {index}")


def _validate_batch_response(response: Any, *, expected_count: int) -> None:
    data = getattr(response, "data", None)
    if data is None or len(data) != expected_count:
        got = 0 if data is None else len(data)
        raise EmbeddingError(f"Embedding API returned {got} results, expected {expected_count}")


def embed_texts(
    texts: list[str],
    *,
    client: OpenAI | None = None,
    model: str = config.EMBEDDING_MODEL,
    batch_size: int = 64,
) -> TextEmbeddingBatch:
    """Embed a flat list of input strings via the OpenAI embeddings API.

    Sends multiple inputs per request (up to `batch_size` per call) rather
    than one request per input. Source order is always preserved: the
    returned `TextEmbeddingBatch.vectors[i]` is the embedding for `texts[i]`,
    regardless of the order the API returns results within a batch (mapped
    via each result's own `index`, not list position).

    Validates every batch response defensively (see `EmbeddingError`): a
    count mismatch, an invalid/duplicate response index, an empty/non-numeric
    vector, or an inconsistent vector dimensionality across batches all raise
    rather than silently producing misaligned embeddings.

    `client` defaults to a real `OpenAI` client built from
    `src.config.OPENAI_API_KEY` (only constructed if actually needed, so unit
    tests that pass a fake `client` never require an API key).
    """
    _validate_batch_size(batch_size)
    if not texts:
        return TextEmbeddingBatch(vectors=[], model=model, usage=EmbeddingUsage())

    active_client = client if client is not None else _get_client()

    vectors: list[list[float] | None] = [None] * len(texts)
    dimensionality: int | None = None
    prompt_tokens_total = 0
    total_tokens_total = 0
    # Each field's completeness is tracked independently: an aggregated
    # field is only a real total if every batch reported that field. One
    # batch missing e.g. total_tokens must not silently zero it out, and
    # must not be masked by another field/batch that *did* report usage.
    prompt_tokens_complete = True
    total_tokens_complete = True
    batch_count = 0

    for batch_start in range(0, len(texts), batch_size):
        batch_texts = texts[batch_start : batch_start + batch_size]
        batch_count += 1
        response = active_client.embeddings.create(model=model, input=batch_texts)
        _validate_batch_response(response, expected_count=len(batch_texts))

        seen_local_indices: set[int] = set()
        for item in response.data:
            local_index = item.index
            if local_index is None or not (0 <= local_index < len(batch_texts)):
                raise EmbeddingError(
                    f"Invalid response index {local_index!r} for a batch of size {len(batch_texts)}"
                )
            if local_index in seen_local_indices:
                raise EmbeddingError(f"Duplicate response index {local_index} within one batch")
            seen_local_indices.add(local_index)

            vector = list(item.embedding)
            _validate_vector(vector, index=batch_start + local_index)
            if dimensionality is None:
                dimensionality = len(vector)
            elif len(vector) != dimensionality:
                raise EmbeddingError(
                    f"Inconsistent embedding dimensionality: expected {dimensionality}, "
                    f"got {len(vector)} at index {batch_start + local_index}"
                )
            vectors[batch_start + local_index] = vector

        usage = getattr(response, "usage", None)
        batch_prompt_tokens = getattr(usage, "prompt_tokens", None) if usage is not None else None
        batch_total_tokens = getattr(usage, "total_tokens", None) if usage is not None else None

        if batch_prompt_tokens is None:
            prompt_tokens_complete = False
        else:
            prompt_tokens_total += batch_prompt_tokens

        if batch_total_tokens is None:
            total_tokens_complete = False
        else:
            total_tokens_total += batch_total_tokens

    missing = [i for i, v in enumerate(vectors) if v is None]
    if missing:
        raise EmbeddingError(f"Missing embeddings for input indices: {missing}")

    return TextEmbeddingBatch(
        vectors=vectors,  # type: ignore[arg-type]  # fully populated, checked above
        model=model,
        usage=EmbeddingUsage(
            prompt_tokens=prompt_tokens_total if prompt_tokens_complete else None,
            total_tokens=total_tokens_total if total_tokens_complete else None,
        ),
    )


def embed_chunks(
    chunks: list[Chunk],
    *,
    client: OpenAI | None = None,
    model: str = config.EMBEDDING_MODEL,
    batch_size: int = 64,
    include_embedding_text: bool = False,
) -> EmbeddingRunResult:
    """Embed a list of Chunks: build each Chunk's derived embedding text
    (`build_embedding_text`), embed them all via `embed_texts`, and map the
    resulting vectors back onto `Chunk.chunk_id` - preserving Chunk order and
    never reordering or duplicating chunk_ids.

    Does not write to Chroma and does not modify `Chunk.text` or the Chunk
    domain model in any way; the returned `EmbeddingRunResult` is a separate,
    standalone typed structure (see module docstring).
    """
    _validate_batch_size(batch_size)
    if not chunks:
        return EmbeddingRunResult(results=[], model=model, batch_count=0, usage=EmbeddingUsage())

    embedding_texts = [build_embedding_text(chunk) for chunk in chunks]
    batch = embed_texts(embedding_texts, client=client, model=model, batch_size=batch_size)

    if len(batch.vectors) != len(chunks):
        # Defensive only: embed_texts already guarantees length == len(texts).
        raise EmbeddingError(
            f"Embedding count {len(batch.vectors)} does not match Chunk count {len(chunks)}"
        )

    results = [
        EmbeddingResult(
            chunk_id=chunk.chunk_id,
            embedding=vector,
            model=model,
            embedding_text=embedding_texts[i] if include_embedding_text else None,
        )
        for i, (chunk, vector) in enumerate(zip(chunks, batch.vectors))
    ]

    return EmbeddingRunResult(
        results=results,
        model=model,
        batch_count=math.ceil(len(chunks) / batch_size),
        usage=batch.usage,
    )


# ============================================================================
# CLI (manual/local validation only - see docs/indexing.md §9-§11)
# ============================================================================


def _load_chunks_from_json(chunks_json_path: Path) -> list[Chunk]:
    data = json.loads(chunks_json_path.read_text(encoding="utf-8"))
    return [Chunk(**c) for c in data["chunks"]]


def main(argv: list[str] | None = None) -> None:
    """Manual/local embedding validation CLI - NOT part of the automated
    test suite. Embeds real Chunks from a *.chunks.json file (produced by
    `src.chunk`) and prints an operational summary only: never the API key,
    never full embedding vectors, never full legal text (see module
    docstring and docs/indexing.md §7/§11).
    """
    parser = argparse.ArgumentParser(
        description="Embed Chunks from a *.chunks.json file via the OpenAI embeddings API "
        "(manual/local validation only - does not write to Chroma)."
    )
    parser.add_argument("chunks_json", type=Path, help="Path to a *.chunks.json produced by src.chunk")
    parser.add_argument("--batch-size", type=int, default=64, help="Embedding requests per batch (default: 64)")
    parser.add_argument(
        "--sample-size",
        type=int,
        default=None,
        help="Embed only the first N Chunks (for a quick, low-cost validation run)",
    )
    args = parser.parse_args(argv)

    if not config.OPENAI_API_KEY:
        print("OPENAI_API_KEY is not set - skipping real embedding call.")
        return

    chunks = _load_chunks_from_json(args.chunks_json)
    if args.sample_size is not None:
        chunks = chunks[: args.sample_size]

    run = embed_chunks(chunks, batch_size=args.batch_size)

    print(f"Input file: {args.chunks_json}")
    print(f"Configured model: {run.model}")
    print(f"Submitted Chunk count: {len(chunks)}")
    print(f"Returned embedding count: {run.input_count}")
    print(f"Vector dimensionality: {run.vector_dimensionality}")
    print(f"Batch count: {run.batch_count}")
    print(f"Prompt tokens: {run.usage.prompt_tokens}")
    print(f"Total tokens: {run.usage.total_tokens}")


if __name__ == "__main__":
    main()
