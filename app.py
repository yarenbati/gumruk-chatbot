"""Streamlit chat interface for the validated end-to-end RAG pipeline."""

from __future__ import annotations

import streamlit as st

from src import config, generate, rag, retrieve, ui


def _render_assistant_message(message: ui.ChatMessage) -> None:
    """Render one stored assistant message without rerunning the backend."""
    if message.get("error"):
        st.error(message["content"])
        return

    if message.get("insufficient_context"):
        st.warning(ui.INSUFFICIENT_CONTEXT_WARNING)
    st.markdown(message["content"])

    citations = message.get("citations", [])
    if citations:
        st.markdown("**Kaynaklar**")
        for citation in citations:
            st.markdown(f"- {citation['display']}")


def _render_message(message: ui.ChatMessage) -> None:
    """Render one persisted chat message."""
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            _render_assistant_message(message)
        else:
            st.markdown(message["content"])


def _render_sidebar() -> None:
    """Render fixed project information and the session-only clear action."""
    with st.sidebar:
        st.header("Hakkında")
        st.write("5326 sayılı Kabahatler Kanunu kapsamındaki indekslenmiş mevzuata dayalı bilgi asistanı.")
        st.caption("Model ve retrieval ayarları merkezi uygulama konfigürasyonundan yönetilir.")
        if st.button("Konuşmayı temizle", use_container_width=True):
            st.session_state.messages = []
            st.rerun()


def _render_examples() -> None:
    """Show non-submitting example questions on an empty first run."""
    st.markdown("**Örnek sorular**")
    for question in ui.EXAMPLE_QUESTIONS:
        st.markdown(f"- {question}")


def main() -> None:
    """Render the Streamlit app and process at most one new question."""
    st.set_page_config(page_title="Gümrük Mevzuatı RAG Asistanı", page_icon="⚖️")
    st.title("Gümrük Mevzuatı RAG Asistanı")
    st.caption("Mevzuat kaynaklarına dayalı bilgi asistanı")
    st.info(ui.DISCLAIMER)
    _render_sidebar()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        _render_message(message)

    if not st.session_state.messages:
        _render_examples()

    question = st.chat_input("Mevzuat hakkında sorunuzu yazın")
    if not question or not question.strip():
        return

    user_message = ui.build_user_message(question)
    st.session_state.messages.append(user_message)
    _render_message(user_message)

    with st.chat_message("assistant"):
        if not config.OPENAI_API_KEY:
            assistant_message = ui.build_error_message(ui.MISSING_API_KEY_MESSAGE)
        else:
            try:
                with st.spinner("Mevzuat kaynakları inceleniyor..."):
                    result = rag.run_rag(question)
                assistant_message = ui.build_assistant_message(result)
            except (retrieve.RetrievalError, generate.GenerationError, rag.RAGPipelineError):
                assistant_message = ui.build_error_message(ui.SAFE_BACKEND_ERROR_MESSAGE)
        _render_assistant_message(assistant_message)
        st.session_state.messages.append(assistant_message)


if __name__ == "__main__":
    main()
