"""Tests for src/generate.py (M6A grounded answer generation + M6B citation
integrity / evidence sufficiency).

All tests are self-contained: they never call OpenAI, never require
`OPENAI_API_KEY`, and never make network calls. `retrieved_chunks` are
plain synthetic `SimpleNamespace` objects (chunk_id/text/metadata) rather
than real `retrieve.RetrievedChunk` instances or a real Chroma collection -
this module is deliberately independently testable without retrieval. The
real 5326 corpus is never used here.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import openai
import pytest

from src import config, generate

# ============================================================================
# Fixture helpers
# ============================================================================


def _rc(chunk_id: str = "c-1", text: str = "Madde 13- (1) Teşebbüs cezalandırılır.", metadata: dict | None = None):
    return SimpleNamespace(chunk_id=chunk_id, text=text, metadata=metadata if metadata is not None else {})


def _envelope(status: str = "YETERLI", answer: str = "Cevap metni. [KAYNAK 1]") -> str:
    """Build a valid `DURUM: .../CEVAP:` envelope string - the format
    `generate_answer()` now requires from every real-call response."""
    return f"DURUM: {status}\nCEVAP:\n{answer}"


class _FakeUsage:
    def __init__(self, input_tokens: Any = None, output_tokens: Any = None, total_tokens: Any = None) -> None:
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.total_tokens = total_tokens


class _FakeContentPart:
    def __init__(self, text: Any) -> None:
        self.text = text
        self.type = "output_text"


class _FakeOutputMessage:
    def __init__(self, content: list[Any]) -> None:
        self.content = content
        self.type = "message"


class _FakeResponse:
    def __init__(
        self,
        *,
        output_text: str | None = None,
        output: list[Any] | None = None,
        model: str = "fake-model",
        usage: Any = None,
    ) -> None:
        self.output_text = output_text
        self.output = output if output is not None else []
        self.model = model
        self.usage = usage


class _FakeResponsesResource:
    """Records every `.create()` call's kwargs; returns a configured
    response, or raises the next exception from `raise_sequence` first."""

    def __init__(self, response: Any = None, *, raise_sequence: list[Exception] | None = None) -> None:
        self._response = response
        self._raise_sequence = list(raise_sequence) if raise_sequence else []
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        if self._raise_sequence:
            exc = self._raise_sequence.pop(0)
            if exc is not None:
                raise exc
        return self._response


class _FakeClient:
    def __init__(self, response: Any = None, *, raise_sequence: list[Exception] | None = None) -> None:
        self.responses = _FakeResponsesResource(response, raise_sequence=raise_sequence)


class _FakeHTTPResponse:
    def __init__(self, status_code: int = 400) -> None:
        self.request = None
        self.status_code = status_code
        self.headers: dict[str, str] = {}


def _bad_request_error(param: str) -> openai.BadRequestError:
    return openai.BadRequestError(
        f"Unsupported parameter: '{param}' is not supported with this model.",
        response=_FakeHTTPResponse(),
        body={"message": "unsupported", "type": "invalid_request_error", "param": param, "code": None},
    )


def _forbidden_client() -> _FakeClient:
    """A fake client whose `.responses.create()` raises if ever called -
    used to prove the zero-context path never reaches the LLM."""

    class _Forbidden:
        def create(self, **kwargs: Any) -> Any:
            raise AssertionError("OpenAI must not be called for empty retrieved_chunks")

    client = SimpleNamespace(responses=_Forbidden())
    return client  # type: ignore[return-value]


# ============================================================================
# 1-3: question validation
# ============================================================================


def test_non_string_question_rejected() -> None:
    with pytest.raises(generate.GenerationError):
        generate.generate_answer(123, [_rc()], client=_FakeClient())  # type: ignore[arg-type]


def test_empty_question_rejected() -> None:
    with pytest.raises(generate.GenerationError):
        generate.generate_answer("", [_rc()], client=_FakeClient())


def test_whitespace_only_question_rejected() -> None:
    with pytest.raises(generate.GenerationError):
        generate.generate_answer("   \n\t  ", [_rc()], client=_FakeClient())


# ============================================================================
# 4-5: zero-context behavior
# ============================================================================


def test_empty_retrieved_chunks_returns_deterministic_insufficient_context() -> None:
    result = generate.generate_answer("Kabahat nedir?", [], client=_FakeClient())
    assert result.insufficient_context is True
    assert result.answer == generate.INSUFFICIENT_CONTEXT_MESSAGE
    assert result.context_chunk_ids == ()
    assert result.citations == ()


def test_empty_context_does_not_call_openai() -> None:
    result = generate.generate_answer("Kabahat nedir?", [], client=_forbidden_client())
    assert result.insufficient_context is True  # no AssertionError raised means OpenAI was never called


# ============================================================================
# 6-14: build_context (pure, no API call)
# ============================================================================


def test_build_context_preserves_retrieval_order() -> None:
    chunks = [_rc(chunk_id="c-1"), _rc(chunk_id="c-2"), _rc(chunk_id="c-3")]
    context = generate.build_context(chunks)
    assert context.index("c-1") < context.index("c-2") < context.index("c-3")
    assert context.index("[KAYNAK 1]") < context.index("[KAYNAK 2]") < context.index("[KAYNAK 3]")


def test_build_context_includes_chunk_id() -> None:
    context = generate.build_context([_rc(chunk_id="5326-madde-13-chunk-001")])
    assert "chunk_id: 5326-madde-13-chunk-001" in context


def test_build_context_includes_legislation_number_when_available() -> None:
    context = generate.build_context([_rc(metadata={"legislation_number": "5326"})])
    assert "mevzuat_no: 5326" in context


def test_build_context_includes_article_no_when_available() -> None:
    context = generate.build_context([_rc(metadata={"article_no": "13"})])
    assert "madde: 13" in context


def test_build_context_includes_article_title_when_available() -> None:
    context = generate.build_context([_rc(metadata={"article_title": "Teşebbüs"})])
    assert "başlık: Teşebbüs" in context


def test_build_context_includes_canonical_text_exactly() -> None:
    text = "Madde 13- (1) Kabahate teşebbüs, kural olarak cezalandırılmaz."
    context = generate.build_context([_rc(text=text)])
    assert text in context


def test_build_context_omits_missing_optional_metadata() -> None:
    context = generate.build_context([_rc(metadata={})])
    assert "mevzuat_no" not in context
    assert "madde:" not in context
    assert "başlık" not in context


def test_build_context_does_not_rewrite_raw_legal_text() -> None:
    text = "Madde 9- (1) Kasten işlenen kabahatler bakımından  kural  budur;  (2) taksir hâli ayrıdır."
    context = generate.build_context([_rc(text=text)])
    assert text in context  # exact substring, including double spaces/punctuation - never normalized


def test_build_context_every_chunk_appears_exactly_once() -> None:
    chunks = [_rc(chunk_id=f"c-{i}") for i in range(4)]
    context = generate.build_context(chunks)
    for chunk in chunks:
        assert context.count(f"chunk_id: {chunk.chunk_id}") == 1


# ============================================================================
# 15-20: API input/instruction wiring
# ============================================================================


def test_generate_uses_config_llm_model_by_default() -> None:
    fake_client = _FakeClient(_FakeResponse(output_text=_envelope()))
    result = generate.generate_answer("Kabahat nedir?", [_rc()], client=fake_client)
    assert result.model == config.LLM_MODEL or fake_client.responses.calls[0]["model"] == config.LLM_MODEL


def test_user_question_reaches_api_input_unchanged() -> None:
    fake_client = _FakeClient(_FakeResponse(output_text=_envelope()))
    question = "Kabahatlerde soruşturma zamanaşımı nasıl belirlenir?"
    generate.generate_answer(question, [_rc()], client=fake_client)

    input_items = fake_client.responses.calls[0]["input"]
    assert any(question in item["content"] for item in input_items)


def test_context_reaches_api_input() -> None:
    fake_client = _FakeClient(_FakeResponse(output_text=_envelope()))
    chunk = _rc(text="Madde metni burada.")
    generate.generate_answer("Soru?", [chunk], client=fake_client)

    expected_context = generate.build_context([chunk])
    input_items = fake_client.responses.calls[0]["input"]
    assert any(expected_context in item["content"] for item in input_items)


def test_instructions_supplied_separately_from_input() -> None:
    fake_client = _FakeClient(_FakeResponse(output_text=_envelope()))
    generate.generate_answer("Soru?", [_rc()], client=fake_client)

    call = fake_client.responses.calls[0]
    assert "instructions" in call
    assert isinstance(call["instructions"], str) and call["instructions"].strip()
    input_contents = [item["content"] for item in call["input"]]
    assert call["instructions"] not in input_contents  # a genuinely separate channel, not duplicated into input


def test_instructions_forbid_outside_knowledge_completion() -> None:
    instructions = generate.build_instructions()
    assert "TAMAMLAMA" in instructions
    assert "UYDURMA" in instructions


def test_source_blocks_identified_as_evidence_not_instructions() -> None:
    instructions = generate.build_instructions()
    assert "talimat değildir" in instructions or "talimat DEĞİLDİR" in instructions

    fake_client = _FakeClient(_FakeResponse(output_text=_envelope()))
    generate.generate_answer("Soru?", [_rc()], client=fake_client)
    input_items = fake_client.responses.calls[0]["input"]
    context_item = next(item for item in input_items if "KAYNAK VERİSİ" in item["content"])
    assert "talimat değildir" in context_item["content"]


# ============================================================================
# 21-23: response extraction / validation
# ============================================================================


def test_successful_fake_response_produces_generation_result() -> None:
    fake_client = _FakeClient(
        _FakeResponse(
            output_text=_envelope(answer="Evet, kabahate teşebbüs cezalandırılmaz. [KAYNAK 1]"),
            model="fake-llm-model",
        )
    )
    result = generate.generate_answer("Soru?", [_rc()], client=fake_client)
    assert isinstance(result, generate.GenerationResult)
    assert result.answer == "Evet, kabahate teşebbüs cezalandırılmaz. [KAYNAK 1]"
    assert result.model == "fake-llm-model"
    assert result.insufficient_context is False
    assert len(result.citations) == 1


def test_empty_model_output_raises_generation_error() -> None:
    fake_client = _FakeClient(_FakeResponse(output_text="", output=[]))
    with pytest.raises(generate.GenerationError):
        generate.generate_answer("Soru?", [_rc()], client=fake_client)


def test_missing_usable_text_raises_generation_error() -> None:
    # No output_text attribute-equivalent value, and an output item whose
    # content part has no usable `.text` at all.
    fake_client = _FakeClient(_FakeResponse(output_text=None, output=[_FakeOutputMessage(content=[SimpleNamespace()])]))
    with pytest.raises(generate.GenerationError):
        generate.generate_answer("Soru?", [_rc()], client=fake_client)


def test_fallback_extraction_from_output_when_output_text_missing() -> None:
    fake_client = _FakeClient(
        _FakeResponse(
            output_text=None,
            output=[_FakeOutputMessage(content=[_FakeContentPart(_envelope(answer="Manuel çıkarım. [KAYNAK 1]"))])],
        )
    )
    result = generate.generate_answer("Soru?", [_rc()], client=fake_client)
    assert result.answer == "Manuel çıkarım. [KAYNAK 1]"


# ============================================================================
# 24-27: context_chunk_ids / usage / latency
# ============================================================================


def test_context_chunk_ids_preserve_input_ordering() -> None:
    chunks = [_rc(chunk_id="c-3"), _rc(chunk_id="c-1"), _rc(chunk_id="c-2")]
    fake_client = _FakeClient(_FakeResponse(output_text=_envelope()))
    result = generate.generate_answer("Soru?", chunks, client=fake_client)
    assert result.context_chunk_ids == ("c-3", "c-1", "c-2")


def test_token_usage_captured_correctly() -> None:
    fake_client = _FakeClient(
        _FakeResponse(output_text=_envelope(), usage=_FakeUsage(input_tokens=120, output_tokens=40, total_tokens=160))
    )
    result = generate.generate_answer("Soru?", [_rc()], client=fake_client)
    assert result.usage.input_tokens == 120
    assert result.usage.output_tokens == 40
    assert result.usage.total_tokens == 160


def test_absent_usage_fields_become_none_not_zero() -> None:
    fake_client = _FakeClient(_FakeResponse(output_text=_envelope(), usage=None))
    result = generate.generate_answer("Soru?", [_rc()], client=fake_client)
    assert result.usage.input_tokens is None
    assert result.usage.output_tokens is None
    assert result.usage.total_tokens is None


def test_partial_usage_fields_stay_none_individually() -> None:
    fake_client = _FakeClient(_FakeResponse(output_text=_envelope(), usage=_FakeUsage(input_tokens=10)))
    result = generate.generate_answer("Soru?", [_rc()], client=fake_client)
    assert result.usage.input_tokens == 10
    assert result.usage.output_tokens is None
    assert result.usage.total_tokens is None


def test_latency_ms_non_negative_when_captured() -> None:
    fake_client = _FakeClient(_FakeResponse(output_text=_envelope()))
    result = generate.generate_answer("Soru?", [_rc()], client=fake_client)
    assert result.latency_ms is not None
    assert result.latency_ms >= 0


def test_latency_ms_is_none_for_zero_context_path() -> None:
    result = generate.generate_answer("Soru?", [], client=_FakeClient())
    assert result.latency_ms is None


# ============================================================================
# 28: fake API path needs no real API key
# ============================================================================


def test_fake_client_path_requires_no_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "OPENAI_API_KEY", None)
    fake_client = _FakeClient(_FakeResponse(output_text=_envelope(answer="Cevap. [KAYNAK 1]")))
    result = generate.generate_answer("Soru?", [_rc()], client=fake_client)
    assert result.answer == "Cevap. [KAYNAK 1]"


# ============================================================================
# 29-30: architecture boundary (static source checks)
# ============================================================================


def _source_text() -> str:
    return Path(inspect.getfile(generate)).read_text(encoding="utf-8")


def _parsed_generate_module() -> ast.Module:
    return ast.parse(_source_text())


def test_generate_module_never_imports_chromadb_or_retrieve() -> None:
    """Checks actual `import`/`from ... import ...` statements via the AST
    - not a raw substring search - so this doesn't false-positive on the
    module docstring's prose (which legitimately explains the retrieve.py
    boundary in English)."""
    imported_module_names: set[str] = set()
    imported_bindings: set[str] = set()
    for node in ast.walk(_parsed_generate_module()):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_module_names.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            imported_module_names.add(node.module or "")
            for alias in node.names:
                imported_bindings.add(alias.name)

    assert not any("chromadb" in name for name in imported_module_names)
    assert not any("retrieve" in name for name in imported_module_names)
    assert not any("retrieve" in name for name in imported_bindings)


def test_generate_module_does_not_reference_embedding_model_or_top_k() -> None:
    """Checks actual attribute-access nodes (e.g. `config.EMBEDDING_MODEL`)
    via the AST - not a raw substring search - so this doesn't
    false-positive on the module docstring's prose explaining that these
    are NOT used here."""
    for node in ast.walk(_parsed_generate_module()):
        if isinstance(node, ast.Attribute):
            assert node.attr not in ("EMBEDDING_MODEL", "TOP_K")


# ============================================================================
# Temperature handling (docs §4/§17, config-driven) - the send/omit
# decision (`_resolve_temperature`) is keyed SOLELY on
# `config.LLM_SEND_TEMPERATURE`, never on a model name/argument. Every test
# here monkeypatches `config.LLM_SEND_TEMPERATURE` explicitly rather than
# relying on .env re-reading at runtime. All via fake exceptions/clients -
# no network.
# ============================================================================


def test_normal_path_omits_temperature_on_first_call_when_flag_false(monkeypatch: pytest.MonkeyPatch) -> None:
    """With the current default (LLM_SEND_TEMPERATURE=false): the normal
    generate_answer() path must omit temperature on the FIRST request -
    never send-then-fail-then-retry."""
    monkeypatch.setattr(config, "LLM_SEND_TEMPERATURE", False)
    fake_client = _FakeClient(_FakeResponse(output_text=_envelope(answer="Cevap. [KAYNAK 1]")))
    result = generate.generate_answer("Soru?", [_rc()], client=fake_client)  # default model + temperature

    assert len(fake_client.responses.calls) == 1  # exactly one Responses API call - no preliminary 400
    assert "temperature" not in fake_client.responses.calls[0]
    assert result.answer == "Cevap. [KAYNAK 1]"


def test_requested_temperature_is_sent_on_first_call_when_flag_true(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "LLM_SEND_TEMPERATURE", True)
    fake_client = _FakeClient(_FakeResponse(output_text=_envelope()))
    generate.generate_answer("Soru?", [_rc()], client=fake_client, temperature=0.3)

    assert len(fake_client.responses.calls) == 1
    assert fake_client.responses.calls[0]["temperature"] == 0.3


def test_resolve_temperature_omits_when_flag_false(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "LLM_SEND_TEMPERATURE", False)
    assert generate._resolve_temperature(config.TEMPERATURE) is None
    assert generate._resolve_temperature(0.7) is None


def test_resolve_temperature_passes_through_when_flag_true(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "LLM_SEND_TEMPERATURE", True)
    assert generate._resolve_temperature(0.7) == 0.7


def test_resolve_temperature_omits_when_none_requested_regardless_of_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(config, "LLM_SEND_TEMPERATURE", True)
    assert generate._resolve_temperature(None) is None
    monkeypatch.setattr(config, "LLM_SEND_TEMPERATURE", False)
    assert generate._resolve_temperature(None) is None


@pytest.mark.parametrize("model", ["model-a", "model-b"])
def test_model_independence_flag_false_never_sends_regardless_of_model(
    monkeypatch: pytest.MonkeyPatch, model: str
) -> None:
    """MODEL-INDEPENDENCE: changing only the `model` argument must never
    change the send/omit decision - this would catch any future
    `if model == ...` regression."""
    monkeypatch.setattr(config, "LLM_SEND_TEMPERATURE", False)
    fake_client = _FakeClient(_FakeResponse(output_text=_envelope()))
    generate.generate_answer("Soru?", [_rc()], client=fake_client, model=model, temperature=0.3)
    assert "temperature" not in fake_client.responses.calls[0]


@pytest.mark.parametrize("model", ["model-a", "model-b"])
def test_model_independence_flag_true_always_sends_regardless_of_model(
    monkeypatch: pytest.MonkeyPatch, model: str
) -> None:
    monkeypatch.setattr(config, "LLM_SEND_TEMPERATURE", True)
    fake_client = _FakeClient(_FakeResponse(output_text=_envelope()))
    generate.generate_answer("Soru?", [_rc()], client=fake_client, model=model, temperature=0.3)
    assert fake_client.responses.calls[0]["temperature"] == 0.3


def test_temperature_omitted_when_none_requested_even_if_flag_true(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "LLM_SEND_TEMPERATURE", True)
    fake_client = _FakeClient(_FakeResponse(output_text=_envelope()))
    generate.generate_answer("Soru?", [_rc()], client=fake_client, temperature=None)
    assert "temperature" not in fake_client.responses.calls[0]


def test_call_responses_api_retries_without_temperature_as_defensive_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Defense-in-depth only: a model that unexpectedly rejects temperature
    even when LLM_SEND_TEMPERATURE=true still gets one clean retry rather
    than a hard failure. This is NOT the normal path when the flag is
    false (see test_normal_path_omits_temperature_on_first_call_when_flag_false)."""
    monkeypatch.setattr(config, "LLM_SEND_TEMPERATURE", True)
    fake_client = _FakeClient(
        _FakeResponse(output_text=_envelope(answer="Cevap. [KAYNAK 1]")),
        raise_sequence=[_bad_request_error("temperature")],
    )
    result = generate.generate_answer("Soru?", [_rc()], client=fake_client, temperature=0.5)
    assert result.answer == "Cevap. [KAYNAK 1]"
    assert len(fake_client.responses.calls) == 2
    assert "temperature" in fake_client.responses.calls[0]
    assert "temperature" not in fake_client.responses.calls[1]


def test_unrelated_bad_request_error_is_not_swallowed() -> None:
    fake_client = _FakeClient(raise_sequence=[_bad_request_error("model")])
    with pytest.raises(generate.GenerationError):
        generate.generate_answer("Soru?", [_rc()], client=fake_client)
    assert len(fake_client.responses.calls) == 1  # no retry for an unrelated param error


def test_no_model_name_hard_coded_for_temperature_capability() -> None:
    """Static guard: `_resolve_temperature` doesn't even take a `model`
    parameter (checked via its real signature, not a docstring/comment
    substring search) - the decision is structurally incapable of being
    keyed on a model name, only on `config.LLM_SEND_TEMPERATURE`."""
    params = inspect.signature(generate._resolve_temperature).parameters
    assert "model" not in params

    # And no literal model-name string appears in the function's actual
    # code statements (docstring excluded) via AST.
    source = inspect.getsource(generate._resolve_temperature)
    func_node = ast.parse(source).body[0]
    assert isinstance(func_node, ast.FunctionDef)
    body_without_docstring = func_node.body[1:] if ast.get_docstring(func_node) else func_node.body
    for node in ast.walk(ast.Module(body=body_without_docstring, type_ignores=[])):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            assert "gpt" not in node.value.lower()


# ============================================================================
# Extra: retrieved_chunks validation edge cases
# ============================================================================


def test_non_sequence_retrieved_chunks_rejected() -> None:
    with pytest.raises(generate.GenerationError):
        generate.generate_answer("Soru?", object(), client=_FakeClient())  # type: ignore[arg-type]


def test_string_retrieved_chunks_rejected() -> None:
    with pytest.raises(generate.GenerationError):
        generate.generate_answer("Soru?", "not-a-list-of-chunks", client=_FakeClient())  # type: ignore[arg-type]


def test_chunk_missing_required_field_rejected() -> None:
    bad_chunk = SimpleNamespace(chunk_id="c-1")  # missing .text/.metadata
    with pytest.raises(generate.GenerationError):
        generate.generate_answer("Soru?", [bad_chunk], client=_FakeClient())


def test_chunk_with_empty_text_rejected() -> None:
    with pytest.raises(generate.GenerationError):
        generate.generate_answer("Soru?", [_rc(text="   ")], client=_FakeClient())


def test_chunk_with_empty_chunk_id_rejected() -> None:
    with pytest.raises(generate.GenerationError):
        generate.generate_answer("Soru?", [_rc(chunk_id="")], client=_FakeClient())


# ============================================================================
# M6B 1-6: parse_generation_envelope
# ============================================================================


def test_envelope_yeterli_parses() -> None:
    status, answer = generate.parse_generation_envelope("DURUM: YETERLI\nCEVAP:\nCevap metni. [KAYNAK 1]")
    assert status == "YETERLI"
    assert answer == "Cevap metni. [KAYNAK 1]"


def test_envelope_yetersiz_parses() -> None:
    status, answer = generate.parse_generation_envelope("DURUM: YETERSIZ\nCEVAP:\nKaynaklar yeterli değil.")
    assert status == "YETERSIZ"
    assert answer == "Kaynaklar yeterli değil."


def test_envelope_missing_durum_raises() -> None:
    with pytest.raises(generate.GenerationFormatError):
        generate.parse_generation_envelope("CEVAP:\nCevap metni.")


def test_envelope_invalid_status_value_raises() -> None:
    with pytest.raises(generate.GenerationFormatError):
        generate.parse_generation_envelope("DURUM: BILINMIYOR\nCEVAP:\nCevap metni.")


def test_envelope_missing_cevap_section_raises() -> None:
    with pytest.raises(generate.GenerationFormatError):
        generate.parse_generation_envelope("DURUM: YETERLI\nCevap metni ama CEVAP: etiketi yok.")


def test_envelope_empty_parsed_answer_raises() -> None:
    with pytest.raises(generate.GenerationFormatError):
        generate.parse_generation_envelope("DURUM: YETERLI\nCEVAP:\n   \n")


def test_generation_format_error_is_a_generation_error() -> None:
    assert issubclass(generate.GenerationFormatError, generate.GenerationError)


# ============================================================================
# M6B 7-9: extract_source_labels
# ============================================================================


def test_extract_single_label() -> None:
    assert generate.extract_source_labels("Metin ... [KAYNAK 1]") == [1]


def test_extract_multiple_labels_in_appearance_order() -> None:
    text = "A ... [KAYNAK 2]. B ... [KAYNAK 1] [KAYNAK 2]"
    assert generate.extract_source_labels(text) == [2, 1, 2]


def test_extract_labels_with_no_citations_returns_empty_list() -> None:
    assert generate.extract_source_labels("Kaynak yok bu cümlede.") == []


# ============================================================================
# M6B: validate_source_labels - dedup, range validation, fail-closed
# ============================================================================


def test_validate_source_labels_deduplicates_preserving_first_appearance() -> None:
    assert generate.validate_source_labels([2, 1, 2], num_chunks=5) == [2, 1]


def test_validate_source_labels_rejects_zero() -> None:
    with pytest.raises(generate.CitationValidationError):
        generate.validate_source_labels([0], num_chunks=5)


def test_validate_source_labels_rejects_out_of_range() -> None:
    with pytest.raises(generate.CitationValidationError):
        generate.validate_source_labels([6], num_chunks=5)
    with pytest.raises(generate.CitationValidationError):
        generate.validate_source_labels([999], num_chunks=5)


def test_validate_source_labels_accepts_exact_last_available_chunk() -> None:
    assert generate.validate_source_labels([5], num_chunks=5) == [5]


def test_citation_validation_error_is_a_generation_error() -> None:
    assert issubclass(generate.CitationValidationError, generate.GenerationError)


# ============================================================================
# M6B 13-19: build_validated_citations - trusted metadata mapping
# ============================================================================


def test_citation_source_number_maps_to_correct_supplied_chunk() -> None:
    chunks = [_rc(chunk_id="c-1"), _rc(chunk_id="c-2"), _rc(chunk_id="c-3")]
    citations = generate.build_validated_citations([2], chunks)
    assert citations[0].source_number == 2
    assert citations[0].chunk_id == "c-2"


def test_citation_chunk_id_comes_from_chunk_object() -> None:
    chunks = [_rc(chunk_id="5326-madde-13-chunk-001")]
    citations = generate.build_validated_citations([1], chunks)
    assert citations[0].chunk_id == "5326-madde-13-chunk-001"


def test_citation_legislation_number_from_metadata() -> None:
    chunks = [_rc(metadata={"legislation_number": "5326"})]
    citations = generate.build_validated_citations([1], chunks)
    assert citations[0].legislation_number == "5326"


def test_citation_article_no_from_metadata() -> None:
    chunks = [_rc(metadata={"article_no": "13"})]
    citations = generate.build_validated_citations([1], chunks)
    assert citations[0].article_no == "13"


def test_citation_article_title_preserved_when_present() -> None:
    chunks = [_rc(metadata={"article_title": "Teşebbüs"})]
    citations = generate.build_validated_citations([1], chunks)
    assert citations[0].article_title == "Teşebbüs"


def test_citation_missing_optional_metadata_stays_none_never_invented() -> None:
    chunks = [_rc(metadata={})]
    citations = generate.build_validated_citations([1], chunks)
    assert citations[0].legislation_number is None
    assert citations[0].article_no is None
    assert citations[0].article_type is None
    assert citations[0].article_title is None
    assert citations[0].paragraph_numbers is None


def test_citation_paragraph_numbers_preserved_when_present() -> None:
    chunks = [_rc(metadata={"paragraph_numbers": ["1", "2"]})]
    citations = generate.build_validated_citations([1], chunks)
    assert citations[0].paragraph_numbers == ("1", "2")


def test_citation_source_label_format() -> None:
    chunks = [_rc()]
    citations = generate.build_validated_citations([1], chunks)
    assert citations[0].source_label == "KAYNAK 1"


# ============================================================================
# render_citation (optional pure rendering helper, docs §11)
# ============================================================================


def test_render_citation_normal_article() -> None:
    citation = generate.ValidatedCitation(
        source_number=1,
        source_label="KAYNAK 1",
        chunk_id="c-1",
        legislation_number="5326",
        article_type="normal",
        article_no="13",
    )
    assert generate.render_citation(citation) == "5326 sayılı Kanun, Madde 13"


def test_render_citation_ek_madde() -> None:
    citation = generate.ValidatedCitation(
        source_number=1,
        source_label="KAYNAK 1",
        chunk_id="c-1",
        legislation_number="5326",
        article_type="ek",
        article_no="1",
    )
    assert generate.render_citation(citation) == "5326 sayılı Kanun, Ek Madde 1"


def test_render_citation_gecici_madde() -> None:
    citation = generate.ValidatedCitation(
        source_number=1,
        source_label="KAYNAK 1",
        chunk_id="c-1",
        legislation_number="5326",
        article_type="gecici",
        article_no="1",
    )
    assert generate.render_citation(citation) == "5326 sayılı Kanun, Geçici Madde 1"


def test_render_citation_never_invents_missing_fields() -> None:
    citation = generate.ValidatedCitation(source_number=1, source_label="KAYNAK 1", chunk_id="c-1")
    rendered = generate.render_citation(citation)
    assert "sayılı Kanun" not in rendered
    assert "Madde" not in rendered


# ============================================================================
# M6B 20-22: citation requirements by status (through generate_answer)
# ============================================================================


def test_yeterli_answer_with_zero_citations_fails_closed() -> None:
    fake_client = _FakeClient(_FakeResponse(output_text=_envelope(status="YETERLI", answer="Cevap ama kaynak yok.")))
    with pytest.raises(generate.CitationValidationError):
        generate.generate_answer("Soru?", [_rc()], client=fake_client)


def test_yeterli_answer_with_valid_citation_succeeds() -> None:
    fake_client = _FakeClient(
        _FakeResponse(output_text=_envelope(status="YETERLI", answer="Cevap metni. [KAYNAK 1]"))
    )
    result = generate.generate_answer("Soru?", [_rc()], client=fake_client)
    assert result.insufficient_context is False
    assert len(result.citations) == 1


def test_yetersiz_answer_with_zero_citations_is_allowed() -> None:
    fake_client = _FakeClient(
        _FakeResponse(output_text=_envelope(status="YETERSIZ", answer="Kaynaklar bu soruyu yanıtlamaya yetmiyor."))
    )
    result = generate.generate_answer("Soru?", [_rc()], client=fake_client)
    assert result.insufficient_context is True
    assert result.citations == ()


# ============================================================================
# M6B 23-26: zero-context vs model-signaled insufficiency
# ============================================================================


def test_zero_retrieved_chunks_causes_zero_api_calls() -> None:
    result = generate.generate_answer("Soru?", [], client=_forbidden_client())
    assert result.insufficient_context is True


def test_zero_retrieved_chunks_returns_insufficient_context_true() -> None:
    result = generate.generate_answer("Soru?", [], client=_FakeClient())
    assert result.insufficient_context is True


def test_model_yetersiz_produces_insufficient_context_true() -> None:
    fake_client = _FakeClient(_FakeResponse(output_text=_envelope(status="YETERSIZ", answer="Yetersiz.")))
    result = generate.generate_answer("Soru?", [_rc()], client=fake_client)
    assert result.insufficient_context is True


def test_model_yeterli_produces_insufficient_context_false() -> None:
    fake_client = _FakeClient(_FakeResponse(output_text=_envelope(status="YETERLI", answer="Yeterli. [KAYNAK 1]")))
    result = generate.generate_answer("Soru?", [_rc()], client=fake_client)
    assert result.insufficient_context is False


# ============================================================================
# M6B 27-28: ordering guarantees
# ============================================================================


def test_context_chunk_ids_still_preserve_retrieval_order_with_citations() -> None:
    chunks = [_rc(chunk_id="c-3"), _rc(chunk_id="c-1"), _rc(chunk_id="c-2")]
    fake_client = _FakeClient(
        _FakeResponse(output_text=_envelope(answer="Cevap. [KAYNAK 2] [KAYNAK 1]"))
    )
    result = generate.generate_answer("Soru?", chunks, client=fake_client)
    assert result.context_chunk_ids == ("c-3", "c-1", "c-2")  # retrieval order, unaffected by citation order


def test_citations_preserve_first_appearance_order_not_retrieval_order() -> None:
    chunks = [_rc(chunk_id="c-3"), _rc(chunk_id="c-1"), _rc(chunk_id="c-2")]
    fake_client = _FakeClient(
        _FakeResponse(output_text=_envelope(answer="Cevap. [KAYNAK 2] önce, [KAYNAK 1] sonra."))
    )
    result = generate.generate_answer("Soru?", chunks, client=fake_client)
    # [KAYNAK 2] cited first in the text -> source_number 2 (-> chunk "c-1") comes first in citations,
    # even though chunk "c-1" is not first in context_chunk_ids' retrieval order.
    assert [c.source_number for c in result.citations] == [2, 1]
    assert [c.chunk_id for c in result.citations] == ["c-1", "c-3"]


# ============================================================================
# M6B 23/29: adversarial citation test - hallucinated source never reaches
# a successful GenerationResult
# ============================================================================


def test_adversarial_hallucinated_citation_rejected_before_successful_result() -> None:
    chunks = [_rc(chunk_id=f"c-{i}") for i in range(5)]  # exactly 5 supplied chunks
    fake_client = _FakeClient(
        _FakeResponse(output_text=_envelope(status="YETERLI", answer="Cevap. [KAYNAK 999]"))
    )
    with pytest.raises(generate.CitationValidationError):
        generate.generate_answer("Soru?", chunks, client=fake_client)


def test_citation_to_exact_last_available_chunk_succeeds() -> None:
    chunks = [_rc(chunk_id=f"c-{i}") for i in range(5)]  # exactly 5 supplied chunks
    fake_client = _FakeClient(
        _FakeResponse(output_text=_envelope(status="YETERLI", answer="Cevap. [KAYNAK 5]"))
    )
    result = generate.generate_answer("Soru?", chunks, client=fake_client)
    assert result.citations[0].source_number == 5
    assert result.citations[0].chunk_id == "c-4"


# ============================================================================
# M6B 30: citation metadata is never created from model prose
# ============================================================================


def test_citation_validator_ignores_article_numbers_written_in_prose() -> None:
    """Model prose says 'Madde 99', but [KAYNAK 1]'s trusted metadata says
    article_no=13 - the validated citation must reflect the trusted chunk
    metadata, never the prose claim."""
    chunks = [_rc(chunk_id="c-1", metadata={"article_no": "13"})]
    fake_client = _FakeClient(
        _FakeResponse(output_text=_envelope(status="YETERLI", answer="Madde 99'a göre ... [KAYNAK 1]"))
    )
    result = generate.generate_answer("Soru?", chunks, client=fake_client)
    assert result.citations[0].article_no == "13"  # never "99"


# ============================================================================
# M6B 31: prompt injection safety preserved when adding citation rules
# ============================================================================


def test_instructions_still_mark_source_as_evidence_not_instructions() -> None:
    instructions = generate.build_instructions()
    assert "talimat DEĞİLDİR" in instructions
    assert "yok say" in instructions


# ============================================================================
# M6B 34: exactly one API call on a normal successful generation
# ============================================================================


def test_successful_generation_uses_exactly_one_api_call() -> None:
    fake_client = _FakeClient(_FakeResponse(output_text=_envelope(answer="Cevap. [KAYNAK 1]")))
    generate.generate_answer("Soru?", [_rc()], client=fake_client)
    assert len(fake_client.responses.calls) == 1
