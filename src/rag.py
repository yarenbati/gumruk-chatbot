"""End-to-end RAG orchestration: question -> retrieval -> generation."""

from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import dataclass
from typing import Any, Callable

from src import config, generate, index, retrieve

if __name__ == "__main__":  # pragma: no cover - manual CLI only
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


class RAGPipelineError(RuntimeError):
    """Raised when retrieval and generation results are inconsistent."""


@dataclass(frozen=True)
class RAGResult:
    """Immutable composition of one retrieval and one generation result."""

    question: str
    retrieval: retrieve.RetrievalResult
    generation: generate.GenerationResult
    retrieved_count: int
    insufficient_context: bool
    citations: tuple[generate.ValidatedCitation, ...]
    total_latency_ms: float


RetrievalCallable = Callable[..., retrieve.RetrievalResult]
GenerationCallable = Callable[..., generate.GenerationResult]


def _validate_question(question: Any) -> None:
    if not isinstance(question, str):
        raise RAGPipelineError(f"question must be a str, got {type(question).__name__}")
    if not question.strip():
        raise RAGPipelineError("question must not be empty or whitespace-only")


def _validate_cross_layer_invariants(
    question: str,
    retrieval_result: retrieve.RetrievalResult,
    generation_result: generate.GenerationResult,
) -> None:
    """Validate identity/order relationships without revalidating semantics."""
    if retrieval_result.query != question:
        raise RAGPipelineError("Retrieval query does not match the original question")
    if generation_result.question != question:
        raise RAGPipelineError("Generation question does not match the original question")

    retrieved_ids = tuple(chunk.chunk_id for chunk in retrieval_result.results)
    if generation_result.context_chunk_ids != retrieved_ids:
        raise RAGPipelineError(
            "Generation context_chunk_ids do not match retrieval results in exact order"
        )

    retrieved_id_set = set(retrieved_ids)
    for citation in generation_result.citations:
        if citation.chunk_id not in retrieved_id_set:
            raise RAGPipelineError(
                f"Validated citation chunk_id {citation.chunk_id!r} is absent from retrieval context"
            )


def run_rag(
    question: str,
    *,
    collection: Any = None,
    embedding_client: Any = None,
    generation_client: Any = None,
    retrieval_fn: RetrievalCallable | None = None,
    generation_fn: GenerationCallable | None = None,
) -> RAGResult:
    """Run exactly one retrieval followed by exactly one generation.

    Supplied retrieval results are passed to generation unchanged and in
    their original order. When ``collection`` is omitted, the existing
    ``src.index`` helpers open the configured production collection. Tests
    can inject a collection, both API clients, or component callables.
    Component exceptions propagate unchanged.
    """
    _validate_question(question)
    start = time.perf_counter()

    active_collection = collection
    if active_collection is None:
        chroma_client = index.get_client()
        active_collection = index.get_collection(chroma_client)

    retrieve_once = retrieval_fn or retrieve.retrieve
    generate_once = generation_fn or generate.generate_answer

    retrieval_result = retrieve_once(
        question,
        collection=active_collection,
        client=embedding_client,
    )
    generation_result = generate_once(
        question,
        retrieval_result.results,
        client=generation_client,
    )

    _validate_cross_layer_invariants(question, retrieval_result, generation_result)
    total_latency_ms = (time.perf_counter() - start) * 1000
    return RAGResult(
        question=question,
        retrieval=retrieval_result,
        generation=generation_result,
        retrieved_count=len(retrieval_result.results),
        insufficient_context=generation_result.insufficient_context,
        citations=generation_result.citations,
        total_latency_ms=total_latency_ms,
    )


def _real_rag_opt_in() -> bool:
    """Return whether the manual CLI may make real OpenAI calls."""
    return bool(config.OPENAI_API_KEY) and os.getenv("RUN_OPENAI_INTEGRATION_TESTS") == "1"


def main(argv: list[str] | None = None) -> None:
    """Run the gated manual RAG CLI and print a compact safe summary."""
    parser = argparse.ArgumentParser(description="Run the end-to-end RAG pipeline")
    parser.add_argument("question", help="User question, passed unchanged")
    args = parser.parse_args(argv)

    if not _real_rag_opt_in():
        print(
            "Real RAG skipped: requires both OPENAI_API_KEY and "
            "RUN_OPENAI_INTEGRATION_TESTS=1."
        )
        return

    result = run_rag(args.question)
    status = "YETERSIZ" if result.insufficient_context else "YETERLI"
    print(f"Question:\n{result.question}\n")
    print(f"Status:\n{status}\n")
    print("Retrieved:")
    for chunk in result.retrieval.results:
        article_no = chunk.metadata.get("article_no", "?")
        print(f"{chunk.rank}. Madde {article_no} | {chunk.chunk_id} | distance={chunk.distance:.4f}")
    print(f"\nAnswer:\n{result.generation.answer}\n")
    print("Validated citations:")
    for citation in result.citations:
        print(f"[{citation.source_label}] -> {generate.render_citation(citation)}")
    retrieval_latency = result.retrieval.latency_ms
    generation_latency = result.generation.latency_ms
    print(f"\nEmbedding usage: {result.retrieval.embedding_usage}")
    print(f"Generation usage: {result.generation.usage}")
    print(f"Retrieval latency: {retrieval_latency if retrieval_latency is not None else 'n/a'} ms")
    print(f"Generation latency: {generation_latency if generation_latency is not None else 'n/a'} ms")
    print(f"Total latency: {result.total_latency_ms:.1f} ms")


if __name__ == "__main__":
    main()
