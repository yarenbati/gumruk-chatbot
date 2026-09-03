"""Offline tests for the M7 end-to-end RAG orchestrator."""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from src import embed, generate, index, rag, retrieve
from src.chunk import Chunk


def _chunk(chunk_id: str = "c-1", article_no: str = "13", distance: float = 0.1) -> retrieve.RetrievedChunk:
    return retrieve.RetrievedChunk(
        rank=1,
        chunk_id=chunk_id,
        text="Madde 13- Kabahate teşebbüs cezalandırılmaz.",
        metadata={"legislation_number": "5326", "article_no": article_no, "article_type": "normal"},
        distance=distance,
    )


def _retrieval(question: str = "Soru?", chunks: list[retrieve.RetrievedChunk] | None = None) -> retrieve.RetrievalResult:
    results = [_chunk()] if chunks is None else chunks
    return retrieve.RetrievalResult(
        query=question,
        model="fake-embedding",
        requested_top_k=5,
        returned_count=len(results),
        results=results,
        embedding_usage=embed.EmbeddingUsage(prompt_tokens=3, total_tokens=3),
        distance_metric="l2",
        latency_ms=1.0,
    )


def _generation(
    question: str = "Soru?",
    ids: tuple[str, ...] = ("c-1",),
    *,
    insufficient: bool = False,
    citations: tuple[generate.ValidatedCitation, ...] | None = None,
) -> generate.GenerationResult:
    citation_tuple = citations
    if citation_tuple is None:
        citation_tuple = () if insufficient else (
            generate.ValidatedCitation(1, "KAYNAK 1", ids[0], "5326", "13", "normal"),
        )
    return generate.GenerationResult(
        question=question,
        answer="Yetersiz." if insufficient else "Yanıt. [KAYNAK 1]",
        model="fake-llm",
        context_chunk_ids=ids,
        citations=citation_tuple,
        usage=generate.GenerationUsage(10, 5, 15),
        latency_ms=2.0,
        insufficient_context=insufficient,
    )


class _Calls:
    def __init__(self, retrieval_result: retrieve.RetrievalResult, generation_result: generate.GenerationResult) -> None:
        self.retrieval_result = retrieval_result
        self.generation_result = generation_result
        self.retrieval: list[tuple[Any, dict[str, Any]]] = []
        self.generation: list[tuple[Any, Any, dict[str, Any]]] = []

    def retrieve(self, question: str, **kwargs: Any) -> retrieve.RetrievalResult:
        self.retrieval.append((question, kwargs))
        return self.retrieval_result

    def generate(self, question: str, chunks: Any, **kwargs: Any) -> generate.GenerationResult:
        self.generation.append((question, chunks, kwargs))
        return self.generation_result


def _run(question: str = "Soru?", *, rr: retrieve.RetrievalResult | None = None, gr: generate.GenerationResult | None = None):
    calls = _Calls(rr or _retrieval(question), gr or _generation(question))
    result = rag.run_rag(
        question,
        collection=object(),
        embedding_client=object(),
        generation_client=object(),
        retrieval_fn=calls.retrieve,
        generation_fn=calls.generate,
    )
    return result, calls


@pytest.mark.parametrize("question", [123, None, object()])
def test_non_string_question_rejected(question: Any) -> None:
    with pytest.raises(rag.RAGPipelineError):
        rag.run_rag(question, collection=object())


@pytest.mark.parametrize("question", ["", "  \n\t "])
def test_empty_question_rejected(question: str) -> None:
    with pytest.raises(rag.RAGPipelineError):
        rag.run_rag(question, collection=object())


def test_exactly_one_retrieval_and_generation_and_unchanged_question() -> None:
    question = "  Özgün soru?  "
    result, calls = _run(question, rr=_retrieval(question), gr=_generation(question))
    assert len(calls.retrieval) == len(calls.generation) == 1
    assert calls.retrieval[0][0] == question
    assert calls.generation[0][0] == question
    assert result.question == question


def test_results_passed_in_exact_order_and_objects_preserved() -> None:
    chunks = [_chunk("c-2"), _chunk("c-1")]
    rr = _retrieval(chunks=chunks)
    gr = _generation(ids=("c-2", "c-1"))
    result, calls = _run(rr=rr, gr=gr)
    assert calls.generation[0][1] is rr.results
    assert result.retrieval is rr
    assert result.generation is gr
    assert result.retrieved_count == 2


@pytest.mark.parametrize("insufficient", [False, True])
def test_status_citations_and_latency_are_composed(insufficient: bool) -> None:
    gr = _generation(insufficient=insufficient)
    result, _ = _run(gr=gr)
    assert result.insufficient_context is insufficient
    assert result.citations is gr.citations
    assert result.total_latency_ms >= 0


def test_empty_results_reach_real_generation_and_do_not_call_llm() -> None:
    rr = _retrieval(chunks=[])

    class ForbiddenResponses:
        def create(self, **kwargs: Any) -> Any:
            raise AssertionError("LLM must not be called")

    result = rag.run_rag(
        "Soru?",
        collection=object(),
        generation_client=SimpleNamespace(responses=ForbiddenResponses()),
        retrieval_fn=lambda question, **kwargs: rr,
    )
    assert result.generation.answer == generate.INSUFFICIENT_CONTEXT_MESSAGE
    assert result.insufficient_context is True


def test_yetersiz_is_not_retried() -> None:
    result, calls = _run(gr=_generation(insufficient=True))
    assert result.insufficient_context is True
    assert len(calls.retrieval) == len(calls.generation) == 1


def test_mismatched_context_order_raises() -> None:
    rr = _retrieval(chunks=[_chunk("c-1"), _chunk("c-2")])
    with pytest.raises(rag.RAGPipelineError, match="exact order"):
        _run(rr=rr, gr=_generation(ids=("c-2", "c-1")))


def test_citation_outside_retrieval_raises() -> None:
    bad = generate.ValidatedCitation(1, "KAYNAK 1", "not-retrieved")
    with pytest.raises(rag.RAGPipelineError, match="absent"):
        _run(gr=_generation(citations=(bad,)))


def test_question_mismatch_raises() -> None:
    with pytest.raises(rag.RAGPipelineError, match="Retrieval query"):
        _run(rr=_retrieval("rewritten"))
    with pytest.raises(rag.RAGPipelineError, match="Generation question"):
        _run(gr=_generation("rewritten"))


@pytest.mark.parametrize("stage", ["retrieval", "generation"])
def test_component_error_propagates_unchanged(stage: str) -> None:
    error = retrieve.RetrievalError("boom") if stage == "retrieval" else generate.GenerationError("boom")

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise error

    kwargs = (
        {"retrieval_fn": fail, "generation_fn": lambda *args, **kwargs: _generation()}
        if stage == "retrieval"
        else {
            "retrieval_fn": lambda *args, **kwargs: _retrieval(),
            "generation_fn": fail,
        }
    )
    with pytest.raises(type(error)) as caught:
        rag.run_rag("Soru?", collection=object(), **kwargs)
    assert caught.value is error


class _EmbeddingItem:
    def __init__(self, index_: int, vector: list[float]) -> None:
        self.index = index_
        self.embedding = vector


class _EmbeddingClient:
    def __init__(self, vector: list[float]) -> None:
        self.calls = 0
        self.vector = vector
        self.embeddings = self

    def create(self, *, model: str, input: list[str]) -> Any:  # noqa: A002
        self.calls += 1
        return SimpleNamespace(
            data=[_EmbeddingItem(i, self.vector) for i, _ in enumerate(input)],
            usage=SimpleNamespace(prompt_tokens=4, total_tokens=4),
        )


class _GenerationClient:
    def __init__(self) -> None:
        self.calls = 0
        self.responses = self

    def create(self, **kwargs: Any) -> Any:
        self.calls += 1
        return SimpleNamespace(
            output_text=(
                "DURUM: YETERLI\nCEVAP:\n"
                "Kabahate teşebbüs kural olarak cezalandırılmaz. [KAYNAK 1]"
            ),
            output=[],
            model="fake-llm",
            usage=SimpleNamespace(input_tokens=10, output_tokens=8, total_tokens=18),
        )


def test_real_component_contracts_compose_with_tmp_chroma(tmp_path: Path) -> None:
    collection = index.get_collection(index.get_client(tmp_path), "m7-contract")
    chunks = [
        Chunk("madde-13", "a13", "doc", "5326", "13", "normal", "Teşebbüs", None,
              "Madde 13- Kabahate teşebbüs cezalandırılmaz.", ["1"], 1, 1, None),
        Chunk("distractor", "a20", "doc", "5326", "20", "normal", "Zamanaşımı", None,
              "Madde 20- Soruşturma zamanaşımı.", ["1"], 2, 2, None),
    ]
    embeddings = [
        embed.EmbeddingResult("madde-13", [0.0, 0.0], "fake-embedding"),
        embed.EmbeddingResult("distractor", [10.0, 10.0], "fake-embedding"),
    ]
    index.index_chunks(chunks, embeddings, collection=collection)
    embedding_client = _EmbeddingClient([0.0, 0.0])
    generation_client = _GenerationClient()

    result = rag.run_rag(
        "Kabahate teşebbüs cezalandırılır mı?",
        collection=collection,
        embedding_client=embedding_client,
        generation_client=generation_client,
    )

    assert result.retrieval.results[0].chunk_id == "madde-13"
    assert result.retrieval.results[0].metadata["article_no"] == "13"
    assert result.citations[0].chunk_id == "madde-13"
    assert result.citations[0].article_no == "13"
    assert result.insufficient_context is False
    assert embedding_client.calls == generation_client.calls == 1


def test_module_has_no_forbidden_architecture_dependencies() -> None:
    tree = ast.parse(Path(rag.__file__).read_text(encoding="utf-8"))
    imports: set[str] = set()
    called_attributes: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add(node.module or "")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            called_attributes.add(node.func.attr)
    assert not any("streamlit" in name or "evaluate" in name for name in imports)
    assert "index_chunks" not in called_attributes
    assert "upsert" not in called_attributes
    assert "add" not in called_attributes
