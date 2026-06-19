from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException, status
from qdrant_client.http.exceptions import ResponseHandlingException

from app.schemas.rag import IngestRequest, IngestResponse, QueryRequest, QueryResponse
from app.services import rag_service

router = APIRouter(prefix="/rag", tags=["rag"])


def _raise_qdrant_http_error(exc: Exception) -> None:
    message = str(exc).lower()
    if "timed out" in message or "timeout" in message:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=(
                "Qdrant request timed out while saving embeddings. "
                "Check QDRANT_URL (cloud clusters should use HTTPS without :6333), "
                "increase QDRANT_TIMEOUT, or lower QDRANT_UPSERT_BATCH_SIZE."
            ),
        ) from exc
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"Qdrant error: {exc}",
    ) from exc


@router.get("/rag-test", status_code=status.HTTP_200_OK)
async def get_rag() -> dict[str, str]:
    return {"message": "RAG API is working"}


@router.post(
    "/ingest-data",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_data(body: IngestRequest) -> IngestResponse:
    """Scrape a URL, chunk content, embed, and store vectors in Qdrant."""

    try:
        return await rag_service.ingest_url(str(body.url))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except (ResponseHandlingException, httpx.TimeoutException, httpx.ConnectTimeout) as exc:
        _raise_qdrant_http_error(exc)


@router.post(
    "/query-data", response_model=QueryResponse, status_code=status.HTTP_200_OK
)
async def query_data(body: QueryRequest) -> QueryResponse:
    """Ask a question; the RAG agent retrieves context from Qdrant and answers."""

    try:
        return await rag_service.query_rag(body.question)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except (ResponseHandlingException, httpx.TimeoutException, httpx.ConnectTimeout) as exc:
        _raise_qdrant_http_error(exc)
