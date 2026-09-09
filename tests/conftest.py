"""Keep normal tests offline and prevent opening production Chroma storage."""

from __future__ import annotations

import os
import socket
from pathlib import Path
from typing import Any

import chromadb
import openai
import pytest

from src import config


@pytest.fixture(autouse=True)
def offline_boundaries(monkeypatch: pytest.MonkeyPatch) -> None:
    """Block network/API access unless real integration tests were opted into."""
    if os.getenv("RUN_OPENAI_INTEGRATION_TESTS") == "1":
        return

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Normal tests must not call OpenAI or the network")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(openai.OpenAI, "__init__", forbidden)
    monkeypatch.setattr(openai.AsyncOpenAI, "__init__", forbidden)
    persistent_client = chromadb.PersistentClient
    production_path = Path(config.CHROMA_PATH).resolve()

    def isolated_client(path: str = "./chroma", *args: Any, **kwargs: Any) -> Any:
        resolved = Path(path).resolve()
        if resolved == production_path or production_path in resolved.parents:
            raise AssertionError("Tests must not open production Chroma storage")
        return persistent_client(path, *args, **kwargs)

    monkeypatch.setattr(chromadb, "PersistentClient", isolated_client)
