from __future__ import annotations

import uuid
from functools import lru_cache

from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.agents.embeddings import get_embeddings
from app.core.config import get_settings


@lru_cache
def get_qdrant_client() -> QdrantClient:
    """Qdrant client with configurable timeout for cloud upserts."""

    settings = get_settings()

    api_key = settings.qdrant_api_key
    url = settings.qdrant_url

    if isinstance(api_key, str) and api_key.strip() == "":
        raise ValueError("QDRANT_API_KEY is not set")

    return QdrantClient(
        url=url,
        api_key=api_key,
        timeout=settings.qdrant_timeout,
    )


def ensure_collection_exists() -> None:
    """Create the configured collection if it does not exist yet."""

    settings = get_settings()
    client = get_qdrant_client()

    if client.collection_exists(settings.collection_name):
        return

    client.create_collection(
        collection_name=settings.collection_name,
        vectors_config=VectorParams(size=settings.vector_size, distance=settings.distance),
    )


def upsert_document_chunks(
    chunks: list[Document],
    vectors: list[list[float]],
) -> int:
    """Upsert embedded chunks in batches to avoid Qdrant Cloud timeouts."""

    if len(chunks) != len(vectors):
        raise ValueError("chunks and vectors length mismatch")

    settings = get_settings()
    client = get_qdrant_client()
    ensure_collection_exists()

    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "page_content": chunk.page_content,
                "metadata": chunk.metadata,
            },
        )
        for chunk, vector in zip(chunks, vectors, strict=True)
    ]

    batch_size = settings.qdrant_upsert_batch_size
    for start in range(0, len(points), batch_size):
        batch = points[start : start + batch_size]
        client.upsert(
            collection_name=settings.collection_name,
            points=batch,
            wait=True,
        )

    return len(points)


def create_collection() -> None:
    """Create the configured collection (no-op if it already exists)."""

    ensure_collection_exists()


@lru_cache
def get_vector_store() -> QdrantVectorStore:
    """Vector store bound to configured collection and embeddings."""

    settings = get_settings()
    collection_name = settings.collection_name

    if isinstance(collection_name, str) and collection_name.strip() == "":
        raise ValueError("Collection name is not set")

    ensure_collection_exists()
    client = get_qdrant_client()

    return QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=get_embeddings(),
    )
