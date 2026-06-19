from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal, Self

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from qdrant_client.models import Distance

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_ENV_FILE = _PROJECT_ROOT / ".env"

# ---------------------------------------------------------------------------
# Single source of truth: Google embed model + vector dimensionality for Qdrant.
# When you switch models, change all three here, mirror in .env / .env.example, then
# recreate the Qdrant collection (dimensions are fixed at collection creation).
# Default: models/gemini-embedding-001 @ 768 dims (see Gemini embeddings docs).
# ---------------------------------------------------------------------------
PROJECT_EMBEDDING_MODEL_ID: str = "models/gemini-embedding-001"
PROJECT_EMBEDDING_VECTOR_DIMENSIONS: int = 768
# Chat model for RAG / agents (Gemini API generateContent)
PROJECT_GEMINI_CHAT_MODEL_ID: str = "models/gemini-2.5-flash"


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE if _ENV_FILE.is_file() else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database Config
    database_url: str = Field(
        ...,
        validation_alias=AliasChoices("DATABASE_URL", "database_url"),
        description="Async SQLAlchemy URL, e.g. postgresql+asyncpg://...",
    )

    # JWT Config
    secret_key: str = Field(
        ..., validation_alias=AliasChoices("SECRET_KEY", "secret_key")
    )
    algorithm: str = Field(
        default="HS256", validation_alias=AliasChoices("ALGORITHM", "algorithm")
    )
    access_token_expire_minutes: int = Field(
        default=60,
        ge=1,
        validation_alias=AliasChoices(
            "ACCESS_TOKEN_EXPIRE_MINUTES", "access_token_expire_minutes"
        ),
    )

    # Google API Config
    google_api_key: str = Field(
        ..., validation_alias=AliasChoices("GOOGLE_API_KEY", "google_api_key")
    )
    gemini_model: str = Field(
        default=PROJECT_GEMINI_CHAT_MODEL_ID,
        validation_alias=AliasChoices("GEMINI_MODEL", "gemini_model"),
    )

    @field_validator("gemini_model", mode="before")
    @classmethod
    def _normalize_gemini_model(cls, value: object) -> object:
        """Ensure models/ prefix and map retired 1.5 ids to a supported chat model."""
        if not isinstance(value, str):
            return value
        v = value.strip()
        if not v:
            return v
        bare = v.removeprefix("models/")
        retired = {
            "gemini-1.5-flash": PROJECT_GEMINI_CHAT_MODEL_ID,
            "gemini-1.5-flash-latest": PROJECT_GEMINI_CHAT_MODEL_ID,
            "gemini-1.5-flash-8b": PROJECT_GEMINI_CHAT_MODEL_ID,
            "gemini-1.5-pro": "models/gemini-2.5-pro",
            "gemini-1.5-pro-latest": "models/gemini-2.5-pro",
        }
        if bare in retired:
            return retired[bare]
        if v.startswith("models/"):
            return v
        return f"models/{bare}"

    gemini_temperature: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        validation_alias=AliasChoices(
            "GEMINI_TEMPERATURE",
            "gemini_temperature",
            "TEMPERATURE",
            "temperature",
        ),
    )
    gemini_max_output_tokens: int = Field(
        default=2048,
        ge=1,
        validation_alias=AliasChoices(
            "GEMINI_MAX_OUTPUT_TOKENS",
            "gemini_max_output_tokens",
            "MAX_OUTPUT_TOKENS",
            "max_output_tokens",
        ),
    )

    embedding_model: str = Field(
        default=PROJECT_EMBEDDING_MODEL_ID,
        validation_alias=AliasChoices("EMBEDDING_MODEL", "embedding_model"),
    )

    @field_validator("embedding_model", mode="before")
    @classmethod
    def _normalize_embedding_model(cls, value: object) -> object:
        """Normalize common aliases to the project default model id."""
        if not isinstance(value, str):
            return value
        v = value.strip()
        aliases = {
            "gemini-embedding-001": PROJECT_EMBEDDING_MODEL_ID,
            "models/gemini-embedding-002": PROJECT_EMBEDDING_MODEL_ID,
            "gemini-embedding-002": PROJECT_EMBEDDING_MODEL_ID,
        }
        if v in aliases:
            return aliases[v]
        return v

    embedding_output_dimensionality: int = Field(
        default=PROJECT_EMBEDDING_VECTOR_DIMENSIONS,
        ge=128,
        le=3072,
        validation_alias=AliasChoices(
            "EMBEDDING_OUTPUT_DIMENSIONALITY",
            "embedding_output_dimensionality",
        ),
        description="Must match VECTOR_SIZE and the embed API output_dimensionality.",
    )

    # Hyperbrowser (LangChain HyperbrowserLoader — scrape/crawl URLs into Documents)
    # https://docs.langchain.com/oss/python/integrations/document_loaders/hyperbrowser
    hyperbrowser_api_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "HYPERBROWSER_API_KEY",
            "hyperbrowser_api_key",
        ),
        description="From https://app.hyperbrowser.ai/ — required to ingest URLs via Hyperbrowser.",
    )
    rag_ingest_urls: str = Field(
        default="",
        validation_alias=AliasChoices("RAG_INGEST_URLS", "rag_ingest_urls"),
        description="Comma-separated URLs for Hyperbrowser scrape/crawl (blogs, docs sites, etc.).",
    )
    hyperbrowser_operation: Literal["scrape", "crawl"] = Field(
        default="scrape",
        validation_alias=AliasChoices(
            "HYPERBROWSER_OPERATION",
            "hyperbrowser_operation",
        ),
        description='HyperbrowserLoader operation: "scrape" (one or many URLs) or "crawl" (single seed URL).',
    )

    # Qdrant Config
    qdrant_url: str = Field(
        ..., validation_alias=AliasChoices("QDRANT_URL", "qdrant_url")
    )
    qdrant_api_key: str = Field(
        ..., validation_alias=AliasChoices("QDRANT_API_KEY", "qdrant_api_key")
    )
    qdrant_timeout: int = Field(
        default=120,
        ge=5,
        validation_alias=AliasChoices("QDRANT_TIMEOUT", "qdrant_timeout"),
        description="HTTP timeout (seconds) for Qdrant Cloud upserts and queries.",
    )
    qdrant_upsert_batch_size: int = Field(
        default=16,
        ge=1,
        le=256,
        validation_alias=AliasChoices(
            "QDRANT_UPSERT_BATCH_SIZE",
            "qdrant_upsert_batch_size",
        ),
        description="Points per upsert request during ingestion (smaller = more reliable on slow links).",
    )
    distance: Distance = Field(
        default=Distance.COSINE, validation_alias=AliasChoices("DISTANCE", "distance")
    )

    vector_size: int = Field(
        default=PROJECT_EMBEDDING_VECTOR_DIMENSIONS,
        validation_alias=AliasChoices("VECTOR_SIZE", "vector_size"),
        description="Qdrant dense vector size; must match embedding_output_dimensionality.",
    )
    collection_name: str = Field(
        default="rag_collection",
        validation_alias=AliasChoices("COLLECTION_NAME", "collection_name"),
    )

    # RAG ingestion / retrieval
    chunk_size: int = Field(
        default=1000,
        ge=1,
        validation_alias=AliasChoices("CHUNK_SIZE", "chunk_size"),
    )
    chunk_overlap: int = Field(
        default=200,
        ge=0,
        validation_alias=AliasChoices("CHUNK_OVERLAP", "chunk_overlap"),
    )
    rag_retrieval_k: int = Field(
        default=4,
        ge=1,
        validation_alias=AliasChoices("RAG_RETRIEVAL_K", "rag_retrieval_k"),
    )

    @field_validator("qdrant_url", mode="after")
    @classmethod
    def _normalize_qdrant_url(cls, value: str) -> str:
        """Qdrant Cloud serves HTTPS on 443; explicit :6333 often causes connect timeouts."""
        url = value.strip().rstrip("/")
        if ".cloud.qdrant.io:6333" in url:
            return url.replace(":6333", "")
        return url

    @field_validator("distance", mode="before")
    @classmethod
    def _coerce_distance(cls, value: object) -> object:
        """Allow .env values like COSINE / cosine (Qdrant Distance uses title-case values)."""
        if isinstance(value, str):
            key = value.strip().upper()
            mapping = {
                "COSINE": Distance.COSINE,
                "DOT": Distance.DOT,
                "EUCLID": Distance.EUCLID,
                "MANHATTAN": Distance.MANHATTAN,
            }
            if key in mapping:
                return mapping[key]
        return value

    @field_validator("hyperbrowser_operation", mode="before")
    @classmethod
    def _normalize_hyperbrowser_operation(cls, value: object) -> object:
        if isinstance(value, str):
            v = value.strip().lower()
            if v in ("scrape", "crawl"):
                return v
        return value

    @model_validator(mode="after")
    def _vector_size_matches_embedding_output(self) -> Self:
        if self.vector_size != self.embedding_output_dimensionality:
            raise ValueError(
                "VECTOR_SIZE and EMBEDDING_OUTPUT_DIMENSIONALITY must match "
                f"(got vector_size={self.vector_size}, "
                f"embedding_output_dimensionality={self.embedding_output_dimensionality}). "
                "Update both to PROJECT_EMBEDDING_VECTOR_DIMENSIONS in config.py (or the same value in .env), "
                "then delete and recreate the Qdrant collection."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
