"""Pure presentation helpers for the Streamlit UI."""

from __future__ import annotations

from typing import Literal, TypedDict

from src import generate, rag

DISCLAIMER = (
    "Bu uygulama yalnızca bilgilendirme amaçlıdır. Hukuki görüş veya bağlayıcı "
    "gümrük kararı niteliği taşımaz. Nihai değerlendirme için yetkili uzman "
    "veya gümrük müşavirine başvurunuz."
)
INSUFFICIENT_CONTEXT_WARNING = (
    "Mevcut getirilen mevzuat kaynakları bu soruyu tam olarak yanıtlamak için yeterli değil."
)
SAFE_BACKEND_ERROR_MESSAGE = "Yanıt oluşturulurken bir hata oluştu. Lütfen tekrar deneyin."
MISSING_API_KEY_MESSAGE = "OPENAI_API_KEY yapılandırılmamış."

EXAMPLE_QUESTIONS = (
    "Kabahat nedir?",
    "Kabahate teşebbüs cezalandırılır mı?",
    "Kabahatlerde soruşturma zamanaşımı süresi nasıl belirlenir?",
    "İdarî para cezasına karşı hangi sürede ve nereye başvurulabilir?",
)


class SerializedCitation(TypedDict):
    """Safe presentation subset of a validated backend citation."""

    source_label: str
    display: str
    legislation_number: str | None
    article_no: str | None
    article_type: str | None
    article_title: str | None


class ChatMessage(TypedDict, total=False):
    """Session-only serialized chat message."""

    role: Literal["user", "assistant"]
    content: str
    insufficient_context: bool
    citations: list[SerializedCitation]
    error: bool


def format_citation(citation: generate.ValidatedCitation) -> str:
    """Format trusted citation metadata for end-user display."""
    base = generate.render_citation(citation)
    if citation.article_title:
        return f"{base} — {citation.article_title}"
    return base


def serialize_citation(citation: generate.ValidatedCitation) -> SerializedCitation:
    """Serialize only safe fields from one validated citation."""
    return {
        "source_label": citation.source_label,
        "display": format_citation(citation),
        "legislation_number": citation.legislation_number,
        "article_no": citation.article_no,
        "article_type": citation.article_type,
        "article_title": citation.article_title,
    }


def build_user_message(question: str) -> ChatMessage:
    """Build a session-state user message without altering its text."""
    return {"role": "user", "content": question}


def build_assistant_message(result: rag.RAGResult) -> ChatMessage:
    """Build a safe assistant message from one authoritative RAG result."""
    return {
        "role": "assistant",
        "content": result.generation.answer,
        "insufficient_context": result.insufficient_context,
        "citations": [serialize_citation(citation) for citation in result.citations],
        "error": False,
    }


def build_error_message(message: str = SAFE_BACKEND_ERROR_MESSAGE) -> ChatMessage:
    """Build a user-safe failure message without backend exception details."""
    return {
        "role": "assistant",
        "content": message,
        "insufficient_context": False,
        "citations": [],
        "error": True,
    }
