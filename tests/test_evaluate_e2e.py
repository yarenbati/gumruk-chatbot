"""Offline tests for the M9A structural end-to-end evaluator."""
from __future__ import annotations
import ast
import hashlib
import inspect
from pathlib import Path
import pytest
from src import embed, evaluate, evaluate_e2e, generate, rag, retrieve

def _question(expected: tuple[str, ...] = ("13",)) -> evaluate.EvaluationQuestion:
    return evaluate.EvaluationQuestion("q-test", "Soru?", expected, frozenset(evaluate.normalize_article_no(a) for a in expected), False)

def _rag_result(articles: tuple[str, ...] = ("13", "20", "21"), *, cited_indexes: tuple[int, ...] = (0,), insufficient: bool = False, answer: str = "Yanıt. [KAYNAK 1]", missing_usage: bool = False) -> rag.RAGResult:
    chunks = [retrieve.RetrievedChunk(i, f"c-{i}", "source text", {"article_no": article}, float(i)) for i, article in enumerate(articles, 1)]
    citations = tuple(generate.ValidatedCitation(i + 1, f"KAYNAK {i + 1}", chunks[i].chunk_id, article_no=chunks[i].metadata["article_no"]) for i in cited_indexes)
    rr = retrieve.RetrievalResult("Soru?", "embedding", 5, len(chunks), chunks, embed.EmbeddingUsage() if missing_usage else embed.EmbeddingUsage(7, 7), "l2", 10.0)
    gr = generate.GenerationResult("Soru?", answer, "llm", tuple(c.chunk_id for c in chunks), citations, generate.GenerationUsage() if missing_usage else generate.GenerationUsage(20, 5, 25), 30.0, insufficient)
    return rag.RAGResult("Soru?", rr, gr, len(chunks), insufficient, citations, 45.0)

def test_dataset_record_preserved_and_file_unchanged() -> None:
    path = Path("tests/questions.json")
    before = hashlib.sha256(path.read_bytes()).digest()
    questions = evaluate.load_questions(path)
    assert len(questions) == 15
    assert (questions[0].id, questions[0].expected_articles, questions[0].expert_validated) == ("q001", ("2",), False)
    assert hashlib.sha256(path.read_bytes()).digest() == before

@pytest.mark.parametrize(("articles", "rank"), [(('13', '20'), 1), (('20', '21', '13'), 3), (('20',), None)])
def test_expected_article_presence_and_rank(articles: tuple[str, ...], rank: int | None) -> None:
    result = evaluate_e2e.evaluate_question(_question(), rag_runner=lambda _: _rag_result(articles, cited_indexes=()))
    assert result.first_expected_rank == rank
    assert result.expected_article_present is (rank is not None)

def test_normalization_and_validated_citation_only_not_answer_prose() -> None:
    result = evaluate_e2e.evaluate_question(_question(("42/A",)), rag_runner=lambda _: _rag_result(("42-a",), answer="Madde 99", cited_indexes=(0,)))
    assert result.cited_articles == ("42-a",) and result.expected_article_present and result.expected_article_cited
    assert "99" not in result.cited_articles

def test_expected_article_cited_false_flags_retrieved_but_not_cited() -> None:
    result = evaluate_e2e.evaluate_question(_question(), rag_runner=lambda _: _rag_result(cited_indexes=(1,)))
    assert not result.expected_article_cited and result.requires_priority_review

@pytest.mark.parametrize(("insufficient", "status"), [(False, "YETERLI"), (True, "YETERSIZ")])
def test_status_is_descriptive_without_correctness_label(insufficient: bool, status: str) -> None:
    indexes = () if insufficient else (0,)
    result = evaluate_e2e.evaluate_question(_question(), rag_runner=lambda _: _rag_result(insufficient=insufficient, cited_indexes=indexes))
    assert result.status == status
    assert not hasattr(result, "sufficiency_accuracy") and not hasattr(result, "legal_accuracy")
    assert result.requires_priority_review is insufficient

def test_missing_expected_is_triage_not_legal_failure() -> None:
    result = evaluate_e2e.evaluate_question(_question(), rag_runner=lambda _: _rag_result(("99",), cited_indexes=(0,)))
    assert result.requires_priority_review and not result.expected_article_present
    assert result.human_review.legal_correctness is None

def test_multiple_expected_requires_all_retrieved_and_cited() -> None:
    question = _question(("13", "20"))
    partial = evaluate_e2e.evaluate_question(question, rag_runner=lambda _: _rag_result(cited_indexes=(0,)))
    clean = evaluate_e2e.evaluate_question(question, rag_runner=lambda _: _rag_result(cited_indexes=(0, 1)))
    assert partial.requires_priority_review and not partial.all_expected_articles_cited
    assert not clean.requires_priority_review

def test_pipeline_error_safe_and_batch_continues() -> None:
    calls = 0
    def runner(_: str) -> rag.RAGResult:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise rag.RAGPipelineError("secret payload vector")
        return _rag_result()
    results, summary = evaluate_e2e.evaluate_all([_question(), _question()], rag_runner=runner)
    assert calls == 2 and len(results) == 2 and summary.error_count == 1 and summary.completed_questions == 1
    assert results[0].status is None and "secret" not in (results[0].error_message_safe or "")

def test_summary_counts_rates_latency_and_tokens() -> None:
    outputs = iter([_rag_result(), _rag_result(("99",), cited_indexes=(), insufficient=True), _rag_result()])
    _, summary = evaluate_e2e.evaluate_all([_question()] * 3, rag_runner=lambda _: next(outputs))
    assert summary.expected_article_present_count == 2 and summary.expected_article_present_rate == pytest.approx(2 / 3)
    assert summary.expected_article_cited_count == 2 and summary.expected_article_cited_rate == pytest.approx(2 / 3)
    assert (summary.yeterli_count, summary.yetersiz_count) == (2, 1)
    assert summary.requires_priority_review_rate == pytest.approx(1 / 3)
    assert summary.human_review_completed_count == 0
    assert summary.human_review_pending_count == 3
    assert (summary.average_retrieval_latency_ms, summary.average_generation_latency_ms, summary.average_pipeline_latency_ms) == (10.0, 30.0, 45.0)
    assert (summary.total_embedding_tokens, summary.total_generation_input_tokens, summary.total_generation_output_tokens, summary.total_generation_tokens) == (21, 60, 15, 75)

def test_missing_usage_is_none_not_fabricated() -> None:
    result = evaluate_e2e.evaluate_question(_question(), rag_runner=lambda _: _rag_result(missing_usage=True))
    summary = evaluate_e2e.summarize([result])
    assert result.embedding_tokens is None and result.generation_total_tokens is None
    assert summary.total_embedding_tokens is None and summary.total_generation_tokens is None

def test_runner_called_exactly_once() -> None:
    calls: list[str] = []
    evaluate_e2e.evaluate_question(_question(), rag_runner=lambda q: calls.append(q) or _rag_result())
    assert calls == ["Soru?"]

def test_architecture_has_no_component_calls_index_or_streamlit() -> None:
    tree = ast.parse(inspect.getsource(evaluate_e2e))
    calls = [node.func for node in ast.walk(tree) if isinstance(node, ast.Call)]
    attrs = {(node.value.id, node.attr) for node in calls if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)}
    assert not ({("retrieve", "retrieve"), ("generate", "generate_answer"), ("index", "index_chunks")} & attrs)
    imported = {alias.name for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names}
    assert "streamlit" not in imported

def test_human_review_fields_are_blank() -> None:
    review = evaluate_e2e.evaluate_question(_question(), rag_runner=lambda _: _rag_result()).human_review
    assert all(value is None for value in review.__dict__.values())
    assert not review.is_complete

def test_q002_shape_requires_priority_review_but_remains_human_review_pending() -> None:
    q002 = evaluate.EvaluationQuestion("q002", "Soru?", ("4",), frozenset({"4"}), False)
    result = evaluate_e2e.evaluate_question(q002, rag_runner=lambda _: _rag_result(("16",), cited_indexes=(0,), insufficient=True))
    summary = evaluate_e2e.summarize([result])
    assert result.requires_priority_review
    assert not result.human_review.is_complete
    assert summary.human_review_completed_count == 0 and summary.human_review_pending_count == 1

def test_no_misleading_human_review_requirement_field_or_wording() -> None:
    source = inspect.getsource(evaluate_e2e)
    assert "requires_human_review" not in source
    assert "Human-review-required rate" not in source
