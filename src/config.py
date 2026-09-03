"""Merkezi konfigürasyon. Tüm ayarlar .env üzerinden environment'tan okunur."""

import os

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

LLM_MODEL = os.getenv("LLM_MODEL", "gpt-5.6-terra")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

TOP_K = int(os.getenv("TOP_K", "5"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0"))

# Whether to actually send `TEMPERATURE` to the configured LLM's Responses
# API calls (see src/generate.py). TEMPERATURE=0 remains the desired value
# regardless; this flag only controls whether it is forwarded to the API
# for the *currently configured* LLM_MODEL. Defaults to "false" because the
# current model is a reasoning-tier model that rejects an explicit
# temperature override outright (HTTP 400). Set LLM_SEND_TEMPERATURE=true
# only when LLM_MODEL is switched to a model that actually supports it.
LLM_SEND_TEMPERATURE = os.getenv("LLM_SEND_TEMPERATURE", "false").strip().lower() == "true"

COLLECTION_NAME = os.getenv("COLLECTION_NAME", "gumruk_mevzuati")

# Local Chroma PersistentClient storage directory (see docs/indexing.md §7).
# Generated runtime state - gitignored, never committed.
CHROMA_PATH = os.getenv("CHROMA_PATH", "chroma")

# Soft chunk-size target (characters, not tokens - no tokenizer dependency)
# used by src/chunk.py's build_chunks(). This is a provisional default for
# legal-semantic chunking, not tuned to any specific embedding model's token
# limit; revisit once an embedding model is chosen (M4).
MAX_CHUNK_CHARS = int(os.getenv("MAX_CHUNK_CHARS", "4000"))
