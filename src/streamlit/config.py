"""Streamlit UI configuration."""

from __future__ import annotations

import os

API_BASE_URL: str = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
API_V1_PREFIX: str = f"{API_BASE_URL}/api/v1"

# Ingestion can scrape, embed, and upsert many chunks — allow a long HTTP timeout.
INGEST_TIMEOUT_SECONDS: float = float(os.getenv("STREAMLIT_INGEST_TIMEOUT", "600"))
QUERY_TIMEOUT_SECONDS: float = float(os.getenv("STREAMLIT_QUERY_TIMEOUT", "120"))
AUTH_TIMEOUT_SECONDS: float = float(os.getenv("STREAMLIT_AUTH_TIMEOUT", "30"))
