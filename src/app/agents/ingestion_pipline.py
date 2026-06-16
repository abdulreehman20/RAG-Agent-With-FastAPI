from __future__ import annotations

from langchain_core.documents import Document
from langchain_core.utils import get_from_env
from langchain_hyperbrowser import HyperbrowserLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.agents.embeddings import get_embeddings
from app.core.config import get_settings
from app.db.vector_store import get_vector_store


async def ingestion_pipline(user_input: str):
    """Loads PDFs, Web Pages, Creates Chunks, Makes embeddings, and Adds it to vector stores"""

    settings = get_settings()
    chunk_size = settings.chunk_size
    chunk_overlap = settings.chunk_overlap

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )

    # Then scrape the from the urls & then splits text & then convert this into chunks
    documents: list[Document] = []

    loader = HyperbrowserLoader(
        urls=user_input,
        api_key=settings.hyperbrowser_api_key,
        operation=settings.hyperbrowser_operation,
    )

    for doc in loader.lazy_load():
        documents.append(doc)
    chunks = text_splitter.split_documents(documents)
    embeddings = get_embeddings().embed_documents(chunks)
    vector_store = get_vector_store()
    vector_store.add_documents(chunks)
    return chunks
