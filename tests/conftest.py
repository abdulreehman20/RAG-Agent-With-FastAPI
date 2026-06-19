"""Pytest fixtures: isolated SQLite DB and TestClient per test."""

from __future__ import annotations

import asyncio

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Fresh app + SQLite file DB so tests never touch DATABASE_URL from .env."""
    db_file = tmp_path / "auth_test.sqlite"
    db_url = f"sqlite+aiosqlite:///{db_file.resolve().as_posix()}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-jwt-signing-32bytes-min")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-api-key")
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
    monkeypatch.setenv("QDRANT_API_KEY", "test-qdrant-api-key")

    from app.core.config import get_settings

    get_settings.cache_clear()

    from app.db.session import reset_engine

    asyncio.run(reset_engine())

    from app.main import create_app

    application = create_app()
    with TestClient(application) as test_client:
        yield test_client

    asyncio.run(reset_engine())
    get_settings.cache_clear()
