from __future__ import annotations

from functools import lru_cache

from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from app.agents.embeddings import get_embeddings
from app.core.config import get_settings


@lru_cache
def get_qdrant_client():
    """Get a Qdrant client."""

    settings = get_settings()

    api_key = settings.qdrant_api_key
    url = settings.qdrant_url

    if isinstance(api_key, str) and api_key.strip() == "":
        raise ValueError("QDRANT_API_KEY is not set")

    return QdrantClient(url=url, api_key=api_key)


@lru_cache
def create_collection():
    """Create a collection."""

    settings = get_settings()
    collection_name = settings.collection_name
    vector_size = settings.vector_size
    distance = settings.distance

    if isinstance(collection_name, str) and collection_name.strip() == "":
        raise ValueError("Collection name is not set")

    if isinstance(vector_size, int) and vector_size <= 0:
        raise ValueError("Vector size must be greater than 0")

    if isinstance(distance, Distance) and distance not in [
        Distance.COSINE,
        Distance.DOT,
    ]:
        raise ValueError("Distance must be either COSINE or DOT")

    client = get_qdrant_client()

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=distance),
    )


@lru_cache
def get_vector_store():
    """Vector store bound to configured collection and embeddings."""

    settings = get_settings()
    collection_name = settings.collection_name

    if isinstance(collection_name, str) and collection_name.strip() == "":
        raise ValueError("Collection name is not set")

    client = get_qdrant_client()

    return QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=get_embeddings(),
    )


# Test these functions
if __name__ == "__main__":

#     print(f"Qdrant client: {get_qdrant_client()}")
#     print(f"Create collection: {create_collection()}")
    print(f"Get vector store: {get_vector_store()}")
