"""Merkezi konfigürasyon. Tüm ayarlar .env üzerinden environment'tan okunur."""

import os

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

LLM_MODEL = os.getenv("LLM_MODEL", "gpt-5.6-terra")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

TOP_K = int(os.getenv("TOP_K", "5"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0"))

COLLECTION_NAME = os.getenv("COLLECTION_NAME", "gumruk_mevzuati")
