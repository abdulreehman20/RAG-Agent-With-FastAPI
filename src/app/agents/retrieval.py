from __future__ import annotations

from langchain_core.documents import Document

from app.core.config import get_settings
from app.db.vector_store import get_vector_store


def retrieval_pipeline(query: str) -> list[Document]:
    """Retrieve top-k document chunks from Qdrant for a user query."""

    settings = get_settings()
    vector_store = get_vector_store()
    retriever = vector_store.as_retriever(search_kwargs={"k": settings.rag_retrieval_k})
    return retriever.invoke(query)
