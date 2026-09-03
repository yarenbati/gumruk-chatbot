"""
Semantic retrieval service (Milestone M5A): user query -> query embedding ->
Chroma nearest-neighbor search -> ranked Chunks.

Scope: query text -> query embedding vector -> Chroma `collection.query()` ->
validated, ranked `RetrievedChunk`s. This module does NOT implement an LLM
call, does NOT generate an answer, does NOT implement citation/refusal logic,
and does NOT compute Recall@K (see `docs/evaluation.md` /
`tests/questions.json`, owned by M5B). See `src/generate.py` for the future
(not-yet-implemented) LLM answer generation step.

Module boundary: `src/chunk.py` (legal parsing/chunking) -> `src/embed.py`
(derived embedding text + OpenAI vectors) -> `src/index.py` (Chroma
persistence) -> `src/retrieve.py` (this module: query -> ranked Chroma
results) -> `src/generate.py` (future M-later LLM generation).

Query contract (docs/architecture.md "Query Flow"): a user query is embedded
exactly as asked - `embed.build_embedding_text()` (document title + article
label + article title enrichment) is document-side only and is NEVER applied
to a query. This module never guesses an article number, prepends a
document title, rewrites/summarizes the question, or injects synthetic
keywords. Query embedding reuses the existing M4A implementation
(`embed.embed_texts`) - there is no second, separate OpenAI embedding
implementation here.

Distance semantics: this module preserves Chroma's raw distance values
exactly as returned and never invents a confidence/similarity/accuracy
percentage from them. The real project collection is configured with
`hnsw:space = "l2"` (squared Euclidean distance - see `_distance_metric`):
smaller is more similar, but the value is not bounded to [0, 1] and is not a
probability. No relevance threshold or abstention rule is implemented here;
that requires a systematic evaluation first (M5B).

Security: the OpenAI API key is read only from `src.config.OPENAI_API_KEY`
(see `src/config.py`); this module never prints, logs, or otherwise
serializes the API key, full embedding vectors, or full legal document text.

CLI usage (manual/local validation only - not part of the automated test
suite; requires BOTH `OPENAI_API_KEY` and `RUN_OPENAI_INTEGRATION_TESTS=1` to
make a real query embedding call, mirroring the same explicit opt-in gate as
src/embed.py and src/index.py - the reusable `retrieve()` function itself
carries no such gate, since the future Streamlit app calls it directly):
    RUN_OPENAI_INTEGRATION_TESTS=1 python -m src.retrieve "Kabahate teşebbüs cezalandırılır mı?"
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import dataclass
from typing import Any

from chromadb.api.models.Collection import Collection

from src import config, embed

if __name__ == "__main__":  # pragma: no cover - exercised via CLI, not tests
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


class RetrievalError(RuntimeError):
    """Raised for invalid retrieval input (non-str/empty query, non-positive
    top_k) or when a Chroma query response cannot be safely aligned into
    RetrievedChunks - e.g. a missing result group, a count mismatch between
    ids/documents/metadatas/distances, an empty chunk_id, or a non-numeric
    distance. Never silently zip mismatched result arrays and risk pairing
    the wrong metadata/text with the wrong chunk_id; raise instead.
    """


# ============================================================================
# Typed results
# ============================================================================


@dataclass(frozen=True)
class RetrievedChunk:
    """One ranked Chroma result (docs/data-model.md `RetrievedChunk`).

    `rank` starts at 1 and follows Chroma's own result order exactly. `text`
    is always Chroma's stored canonical document (`Chunk.text`) - never the
    derived embedding text. `distance` is the raw, unmodified value Chroma
    returned - never converted into a similarity/confidence/accuracy score
    (see module docstring).
    """

    rank: int
    chunk_id: str
    text: str
    metadata: dict[str, Any]
    distance: float


@dataclass(frozen=True)
class RetrievalResult:
    """Summary of one `retrieve()` run.

    `distance_metric` is a best-effort read of the collection's actual
    configured metric (see `_distance_metric`) for reporting/documentation
    only - `None` if it cannot be reliably obtained, never guessed.
    `latency_ms` covers the embedding call plus the Chroma query.
    """

    query: str
    model: str
    requested_top_k: int
    returned_count: int
    results: list[RetrievedChunk]
    embedding_usage: embed.EmbeddingUsage
    distance_metric: str | None = None
    latency_ms: float | None = None


# ============================================================================
# Input validation
# ============================================================================


def _validate_query(query: Any) -> None:
    if not isinstance(query, str):
        raise RetrievalError(f"query must be a str, got {type(query).__name__}")
    if not query.strip():
        raise RetrievalError("query must not be empty or whitespace-only")


def _validate_top_k(top_k: int) -> None:
    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k <= 0:
        raise RetrievalError(f"top_k must be a positive int, got {top_k!r}")


# ============================================================================
# A. Query embedding (docs/indexing.md embedding provider boundary)
# ============================================================================


def embed_query(
    query: str,
    *,
    client: Any = None,
    model: str = config.EMBEDDING_MODEL,
) -> tuple[list[float], str, embed.EmbeddingUsage]:
    """Embed one raw user query string via `embed.embed_texts` (M4A) -
    reuses the existing OpenAI embedding implementation rather than a
    second, separate one.

    The query is sent to `embed_texts` exactly as given - no document-side
    embedding enrichment (`embed.build_embedding_text`: document title,
    article label, article title) is ever applied to a user query, and the
    question is never rewritten, summarized, or keyword-injected.

    Validates that exactly one non-empty, fully numeric vector is returned;
    raises `RetrievalError` otherwise. `client` defaults to a real `OpenAI`
    client built lazily inside `embed_texts` (only constructed if actually
    needed, so tests that pass a fake `client` never require an API key).
    """
    _validate_query(query)

    batch = embed.embed_texts([query], client=client, model=model, batch_size=1)

    if len(batch.vectors) != 1:
        raise RetrievalError(f"Expected exactly one query embedding vector, got {len(batch.vectors)}")

    vector = batch.vectors[0]
    if not isinstance(vector, (list, tuple)) or len(vector) == 0:
        raise RetrievalError("Query embedding vector is empty or invalid")
    if not all(isinstance(v, (int, float)) for v in vector):
        raise RetrievalError("Query embedding vector contains non-numeric elements")

    return list(vector), batch.model, batch.usage


# ============================================================================
# B. Vector search (Chroma query)
# ============================================================================


def _distance_metric(collection: Collection) -> str | None:
    """Best-effort read of the collection's actual configured distance
    metric (e.g. Chroma's `hnsw:space`), for reporting/documentation only -
    never guessed, and never used to reinterpret a raw distance value.
    Returns `None` if it cannot be reliably obtained (e.g. an older Chroma
    version without `configuration_json`).
    """
    try:
        space = collection.configuration_json.get("hnsw", {}).get("space")
        if space:
            return str(space)
    except Exception:
        pass
    try:
        space = (collection.metadata or {}).get("hnsw:space")
        if space:
            return str(space)
    except Exception:
        pass
    return None


def _validate_and_build_results(response: dict[str, Any]) -> list[RetrievedChunk]:
    """Safely validate a one-query Chroma `query()` response and build
    ranked `RetrievedChunk`s in Chroma's own order (rank 1 = nearest).

    Defensive per §12 of the M5A contract: raises `RetrievalError` rather
    than silently zipping mismatched ids/documents/metadatas/distances,
    which could otherwise pair the wrong article metadata with the wrong
    text.
    """
    ids_groups = response.get("ids")
    if not isinstance(ids_groups, list) or len(ids_groups) != 1:
        got = 0 if not isinstance(ids_groups, list) else len(ids_groups)
        raise RetrievalError(f"Expected exactly one Chroma result group, got {got}")
    ids = ids_groups[0]

    def _one_group(key: str) -> list[Any] | None:
        groups = response.get(key)
        if not groups:
            return None
        if len(groups) != 1:
            raise RetrievalError(f"Expected exactly one Chroma '{key}' group, got {len(groups)}")
        return groups[0]

    documents = _one_group("documents")
    metadatas = _one_group("metadatas")
    distances = _one_group("distances")

    if documents is None or len(documents) != len(ids):
        raise RetrievalError(
            f"Chroma documents ({0 if documents is None else len(documents)}) "
            f"do not align with ids ({len(ids)})"
        )
    if metadatas is None or len(metadatas) != len(ids):
        raise RetrievalError(
            f"Chroma metadatas ({0 if metadatas is None else len(metadatas)}) "
            f"do not align with ids ({len(ids)})"
        )
    if distances is None or len(distances) != len(ids):
        raise RetrievalError(
            f"Chroma distances ({0 if distances is None else len(distances)}) "
            f"do not align with ids ({len(ids)})"
        )

    results: list[RetrievedChunk] = []
    for rank, (chunk_id, text, metadata, distance) in enumerate(zip(ids, documents, metadatas, distances), start=1):
        if not chunk_id:
            raise RetrievalError(f"Empty or missing chunk_id at rank {rank}")
        if text is None:
            raise RetrievalError(f"Missing document text for chunk_id {chunk_id!r}")
        if isinstance(distance, bool) or not isinstance(distance, (int, float)):
            raise RetrievalError(f"Non-numeric distance for chunk_id {chunk_id!r}: {distance!r}")
        results.append(
            RetrievedChunk(
                rank=rank,
                chunk_id=chunk_id,
                text=text,
                metadata=dict(metadata) if metadata else {},
                distance=float(distance),
            )
        )
    return results


def retrieve_by_embedding(
    query_vector: list[float],
    *,
    collection: Collection,
    top_k: int = config.TOP_K,
    where: dict[str, Any] | None = None,
) -> list[RetrievedChunk]:
    """Query Chroma with a precomputed query vector and return ranked,
    validated `RetrievedChunk`s.

    Always queries with `query_embeddings=` (never `query_texts=`), matching
    the collection's `embedding_function=None` configuration (docs/indexing.md
    §3). Requests only `documents`/`metadatas`/`distances` - ids are always
    returned by Chroma and full stored embedding vectors are never requested
    for normal retrieval.

    `top_k` is capped to the collection's current record count - never
    fabricates extra results when the collection has fewer records than
    `top_k` (e.g. count=3, top_k=5 -> 3 results). An empty collection
    returns an empty list rather than failing.

    `where` is passed straight through to Chroma for optional metadata
    filtering (default `None` - unfiltered); no filter is ever inferred from
    the query text here.
    """
    _validate_top_k(top_k)

    count = collection.count()
    if count == 0:
        return []

    effective_top_k = min(top_k, count)

    response = collection.query(
        query_embeddings=[query_vector],
        n_results=effective_top_k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    return _validate_and_build_results(response)


# ============================================================================
# C. Orchestration
# ============================================================================


def retrieve(
    query: str,
    *,
    collection: Collection,
    client: Any = None,
    model: str = config.EMBEDDING_MODEL,
    top_k: int = config.TOP_K,
    where: dict[str, Any] | None = None,
) -> RetrievalResult:
    """Orchestrate A (`embed_query`) + B (`retrieve_by_embedding`): a raw
    user query in, a `RetrievalResult` of ranked Chunks out. No LLM call, no
    generated answer, no citations - see module docstring for scope.

    This is the reusable, production entry point the future Streamlit app
    calls directly - it carries no `RUN_OPENAI_INTEGRATION_TESTS` gate
    itself (that opt-in gate belongs only to this module's manual CLI, see
    `main`/`_real_retrieval_opt_in`).
    """
    _validate_query(query)
    _validate_top_k(top_k)

    start = time.perf_counter()
    vector, used_model, usage = embed_query(query, client=client, model=model)
    results = retrieve_by_embedding(vector, collection=collection, top_k=top_k, where=where)
    latency_ms = (time.perf_counter() - start) * 1000

    return RetrievalResult(
        query=query,
        model=used_model,
        requested_top_k=top_k,
        returned_count=len(results),
        results=results,
        embedding_usage=usage,
        distance_metric=_distance_metric(collection),
        latency_ms=latency_ms,
    )


# ============================================================================
# CLI (manual/local validation only - see module docstring)
# ============================================================================


def _real_retrieval_opt_in() -> bool:
    """Explicit opt-in gate for the MANUAL CLI only (see module docstring) -
    a real query embedding call is only ever made when BOTH
    `config.OPENAI_API_KEY` is available AND `RUN_OPENAI_INTEGRATION_TESTS=1`
    is set. This mirrors src/embed.py's and src/index.py's real-API gates.
    The reusable `retrieve()` function above carries no such gate.
    """
    return bool(config.OPENAI_API_KEY) and os.getenv("RUN_OPENAI_INTEGRATION_TESTS") == "1"


def _format_result_line(chunk: RetrievedChunk) -> str:
    article_no = chunk.metadata.get("article_no")
    article_type = chunk.metadata.get("article_type", "normal")
    try:
        label = embed.build_article_label(article_type, article_no) if article_no else None
    except ValueError:
        label = None
    label_part = f" | {label}" if label else ""

    title = chunk.metadata.get("article_title")
    title_part = f" | {title}" if title else ""

    return f"{chunk.rank}. {chunk.chunk_id}{label_part}{title_part} | distance={chunk.distance:.4f}"


def main(argv: list[str] | None = None) -> None:
    """Manual/local retrieval CLI - NOT part of the automated test suite.
    Embeds a real query and runs a real Chroma search, but only when
    explicit opt-in is enabled (see `_real_retrieval_opt_in`); otherwise
    exits cleanly before calling OpenAI. Prints a compact summary only:
    never the API key, never full vectors, never full Chunk.text.
    """
    from src import index  # local import: keeps `src.index`/chromadb client setup CLI-only here

    parser = argparse.ArgumentParser(description="Run a semantic retrieval query against the local Chroma collection.")
    parser.add_argument("query", help="User question (sent as-is, no enrichment)")
    parser.add_argument("--top-k", type=int, default=config.TOP_K, help=f"Number of results (default: {config.TOP_K})")
    args = parser.parse_args(argv)

    if not _real_retrieval_opt_in():
        print(
            "Real retrieval skipped: requires both OPENAI_API_KEY and "
            "RUN_OPENAI_INTEGRATION_TESTS=1 (explicit opt-in not enabled or "
            "credentials unavailable)."
        )
        return

    client = index.get_client()
    collection = index.get_collection(client)
    result = retrieve(args.query, collection=collection, top_k=args.top_k)

    print(f"Query: {result.query}")
    print(f"Model: {result.model}")
    print(f"Returned: {result.returned_count}")
    for chunk in result.results:
        print(_format_result_line(chunk))


if __name__ == "__main__":
    main()
