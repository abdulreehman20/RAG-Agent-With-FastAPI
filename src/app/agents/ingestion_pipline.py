from __future__ import annotations

import asyncio

from langchain_core.documents import Document
from langchain_core.utils import get_from_env
from langchain_hyperbrowser import HyperbrowserLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.agents.embeddings import get_embeddings
from app.core.config import get_settings
from app.db.vector_store import upsert_document_chunks


def _resolve_hyperbrowser_api_key(api_key: str) -> str:
    key = (api_key or "").strip()
    if key:
        return key
    return (
        get_from_env("HYPERBROWSER_API_KEY", env_key="HYPERBROWSER_API_KEY") or ""
    ).strip()


async def ingestion_pipline(url: str) -> dict[str, int | str]:
    """Load a URL via Hyperbrowser, chunk, embed, and persist chunks in Qdrant."""

    settings = get_settings()

    api_key = _resolve_hyperbrowser_api_key(settings.hyperbrowser_api_key)
    if not api_key:
        raise ValueError(
            "HYPERBROWSER_API_KEY is not set. Add it to .env (https://app.hyperbrowser.ai/)."
        )

    # --- Stage 1: Load website data ---
    print("\n=== Stage 1: Load Website Data ===")
    loader = HyperbrowserLoader(
        urls=url.strip(),
        api_key=api_key,
        operation=settings.hyperbrowser_operation,
    )

    documents: list[Document] = await loader.aload()

    if not documents:
        raise ValueError(f"No content loaded from URL: {url}")

    for index, document in enumerate(documents, start=1):
        print(f"\n--- Document {index} ---")
        print(f"Metadata: {document.metadata}")
        print(f"Content preview:\n{document.page_content[:500]}")
        if len(document.page_content) > 500:
            print("...")

    # --- Stage 2: Chunk the document ---
    print("\n=== Stage 2: Chunk the Document ===")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    chunks = text_splitter.split_documents(documents)

    for chunk in chunks:
        chunk.metadata["source"] = url.strip()

    for index, chunk in enumerate(chunks, start=1):
        print(f"\n--- Chunk {index}/{len(chunks)} ---")
        print(f"Metadata: {chunk.metadata}")
        print(chunk.page_content)

    print(f"\nTotal chunks: {len(chunks)}")

    # --- Stage 3: Generate embeddings and store in Qdrant ---
    print("\n=== Stage 3: Generate Embeddings & Store in Qdrant ===")

    embeddings_model = get_embeddings()

    texts = [chunk.page_content for chunk in chunks]
    vectors = embeddings_model.embed_documents(texts)

    for index, vector in enumerate(vectors, start=1):
        preview = ", ".join(f"{value:.6f}" for value in vector[:8])
        print(f"Embedding {index}: dims={len(vector)}, values=[{preview}, ...]")

    chunks_saved = await asyncio.to_thread(upsert_document_chunks, chunks, vectors)

    print(
        f"\nSuccess: {chunks_saved} chunk(s) converted to embeddings and saved "
        f"to Qdrant collection '{settings.collection_name}'."
    )

    return {
        "url": url.strip(),
        "documents_loaded": len(documents),
        "chunks_created": len(chunks),
        "chunks_saved": chunks_saved,
        "collection": settings.collection_name,
    }


if __name__ == "__main__":
    asyncio.run(
        ingestion_pipline(
            "https://www.abduls.xyz/blogs/intro-to-retrieval-augmented-generation"
        )
    )
