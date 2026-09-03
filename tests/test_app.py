"""Offline behavior and architecture tests for the Streamlit UI."""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from streamlit.testing.v1 import AppTest

from src import config, generate, rag, ui

APP_PATH = Path(__file__).parents[1] / "app.py"


def _citation(**overrides: Any) -> generate.ValidatedCitation:
    values = {
        "source_number": 1,
        "source_label": "KAYNAK 1",
        "chunk_id": "5326-madde-13-chunk-001",
        "legislation_number": "5326",
        "article_no": "13",
        "article_type": "normal",
        "article_title": "Teşebbüs",
    }
    values.update(overrides)
    return generate.ValidatedCitation(**values)


def _result(*, insufficient: bool = False, citations: tuple[Any, ...] | None = None) -> Any:
    return SimpleNamespace(
        generation=SimpleNamespace(answer="Destekli yanıt. [KAYNAK 1]"),
        insufficient_context=insufficient,
        citations=(_citation(),) if citations is None else citations,
    )


def test_initial_app_starts_without_rag_call(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rag, "run_rag", lambda question: pytest.fail("RAG must not run at startup"))
    app = AppTest.from_file(str(APP_PATH)).run()
    assert not app.exception
    assert app.session_state["messages"] == []
    assert app.chat_input


def test_citation_format_uses_trusted_metadata_and_title() -> None:
    assert ui.format_citation(_citation()) == "5326 sayılı Kanun, Madde 13 — Teşebbüs"


def test_missing_optional_citation_metadata_is_safe() -> None:
    citation = _citation(legislation_number=None, article_no=None, article_type=None, article_title=None)
    assert ui.format_citation(citation) == "[KAYNAK 1]"


@pytest.mark.parametrize("insufficient", [False, True])
def test_assistant_state_preserves_status_and_partial_citations(insufficient: bool) -> None:
    message = ui.build_assistant_message(_result(insufficient=insufficient))
    assert message["insufficient_context"] is insufficient
    assert message["citations"][0]["article_no"] == "13"


def test_history_serialization_contains_only_safe_presentation_data() -> None:
    serialized = repr(ui.build_assistant_message(_result()))
    assert "api_key" not in serialized.lower()
    assert "embedding" not in serialized.lower()
    assert "raw_response" not in serialized.lower()
    assert "chunk_id" not in serialized.lower()


def test_safe_error_message_hides_exception_details() -> None:
    message = ui.build_error_message()
    assert message["error"] is True
    assert message["content"] == ui.SAFE_BACKEND_ERROR_MESSAGE


def test_blank_question_never_calls_rag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "OPENAI_API_KEY", "fake-test-key")
    monkeypatch.setattr(rag, "run_rag", lambda question: pytest.fail("blank input must not call RAG"))
    app = AppTest.from_file(str(APP_PATH)).run()
    app.chat_input[0].set_value("   ").run()
    assert app.session_state["messages"] == []


def test_one_submission_calls_rag_once_and_history_rerun_does_not_recall(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(config, "OPENAI_API_KEY", "fake-test-key")

    def fake_run(question: str) -> Any:
        calls.append(question)
        return _result()

    monkeypatch.setattr(rag, "run_rag", fake_run)
    app = AppTest.from_file(str(APP_PATH)).run()
    app.chat_input[0].set_value("Kabahate teşebbüs cezalandırılır mı?").run()
    assert calls == ["Kabahate teşebbüs cezalandırılır mı?"]
    assert len(app.session_state["messages"]) == 2
    app.run()
    assert len(calls) == 1


def test_yetersiz_renders_warning_and_partial_citation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "OPENAI_API_KEY", "fake-test-key")
    monkeypatch.setattr(rag, "run_rag", lambda question: _result(insufficient=True))
    app = AppTest.from_file(str(APP_PATH)).run()
    app.chat_input[0].set_value("Eksik kaynaklı soru").run()
    assert any(ui.INSUFFICIENT_CONTEXT_WARNING in warning.value for warning in app.warning)
    assert app.session_state["messages"][-1]["citations"][0]["article_no"] == "13"


def test_missing_api_key_is_safe_and_skips_rag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "OPENAI_API_KEY", None)
    monkeypatch.setattr(rag, "run_rag", lambda question: pytest.fail("RAG must not run without key"))
    app = AppTest.from_file(str(APP_PATH)).run()
    app.chat_input[0].set_value("Soru?").run()
    assert app.session_state["messages"][-1]["content"] == ui.MISSING_API_KEY_MESSAGE
    assert app.session_state["messages"][-1]["error"] is True


def test_backend_error_becomes_safe_ui_message(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "OPENAI_API_KEY", "fake-test-key")

    def fail(question: str) -> Any:
        raise rag.RAGPipelineError("sensitive internal detail")

    monkeypatch.setattr(rag, "run_rag", fail)
    app = AppTest.from_file(str(APP_PATH)).run()
    app.chat_input[0].set_value("Soru?").run()
    message = app.session_state["messages"][-1]
    assert message["content"] == ui.SAFE_BACKEND_ERROR_MESSAGE
    assert "sensitive" not in message["content"]


def test_clear_chat_clears_messages_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "OPENAI_API_KEY", "fake-test-key")
    monkeypatch.setattr(rag, "run_rag", lambda question: _result())
    app = AppTest.from_file(str(APP_PATH)).run()
    app.chat_input[0].set_value("Soru?").run()
    assert app.session_state["messages"]
    clear_button = next(button for button in app.button if button.label == "Konuşmayı temizle")
    clear_button.click().run()
    assert app.session_state["messages"] == []


def test_app_architecture_uses_only_rag_backend_entrypoint() -> None:
    tree = ast.parse(APP_PATH.read_text(encoding="utf-8"))
    imported_modules: set[str] = set()
    calls: list[tuple[str, str]] = []
    string_literals: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.add(node.module or "")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            calls.append((node.func.value.id, node.func.attr))
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            string_literals.add(node.value)

    assert calls.count(("rag", "run_rag")) == 1
    assert ("retrieve", "retrieve") not in calls
    assert ("generate", "generate_answer") not in calls
    assert not any(name.endswith("evaluate") or "chromadb" in name or "openai" in name for name in imported_modules)
    assert not any(call in calls for call in [("index", "index_chunks"), ("collection", "upsert")])
    assert not any("text-embedding-" in value or value.startswith("gpt-") for value in string_literals)
