from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl


class IngestRequest(BaseModel):
    url: HttpUrl = Field(
        description="Website or blog URL to scrape and index in Qdrant"
    )


class IngestResponse(BaseModel):
    url: str
    documents_loaded: int
    chunks_created: int
    chunks_saved: int
    collection: str


class QueryRequest(BaseModel):
    question: str = Field(
        min_length=1, max_length=4000, description="User question for the RAG agent"
    )


class QueryResponse(BaseModel):
    question: str
    answer: str
