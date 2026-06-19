from __future__ import annotations

from app.agents.agent import ask_agent
from app.agents.ingestion_pipline import ingestion_pipline
from app.schemas.rag import IngestResponse, QueryResponse


async def ingest_url(url: str) -> IngestResponse:
    """Run the ingestion pipeline for a single URL and persist chunks in Qdrant."""

    summary = await ingestion_pipline(url)
    return IngestResponse.model_validate(summary)


async def query_rag(question: str) -> QueryResponse:
    """Run the RAG agent for a user question and return the generated answer."""

    answer = await ask_agent(question)
    return QueryResponse(question=question, answer=answer)
