"""Tests for RAG ingest and query API routes."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from starlette.testclient import TestClient

RAG = "/api/v1/rag"


def test_rag_test_endpoint(client: TestClient) -> None:
    response = client.get(f"{RAG}/rag-test")
    assert response.status_code == 200
    assert response.json() == {"message": "RAG API is working"}


@patch("app.services.rag_service.ingestion_pipline", new_callable=AsyncMock)
def test_ingest_data_returns_summary(
    mock_ingest: AsyncMock, client: TestClient
) -> None:
    mock_ingest.return_value = {
        "url": "https://example.com/blog",
        "documents_loaded": 1,
        "chunks_created": 3,
        "chunks_saved": 3,
        "collection": "rag_collection",
    }

    response = client.post(
        f"{RAG}/ingest-data",
        json={"url": "https://example.com/blog"},
    )

    assert response.status_code == 201, response.text
    assert response.json() == {
        "url": "https://example.com/blog",
        "documents_loaded": 1,
        "chunks_created": 3,
        "chunks_saved": 3,
        "collection": "rag_collection",
    }
    mock_ingest.assert_awaited_once_with("https://example.com/blog")


@patch("app.services.rag_service.ingestion_pipline", new_callable=AsyncMock)
def test_ingest_data_value_error_returns_400(
    mock_ingest: AsyncMock, client: TestClient
) -> None:
    mock_ingest.side_effect = ValueError("No content loaded from URL")

    response = client.post(
        f"{RAG}/ingest-data",
        json={"url": "https://example.com/empty"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "No content loaded from URL"


@patch("app.services.rag_service.ask_agent", new_callable=AsyncMock)
def test_query_data_returns_answer(mock_ask: AsyncMock, client: TestClient) -> None:
    mock_ask.return_value = "RAG retrieves context before generating an answer."

    response = client.post(
        f"{RAG}/query-data",
        json={"question": "What is RAG?"},
    )

    assert response.status_code == 200, response.text
    assert response.json() == {
        "question": "What is RAG?",
        "answer": "RAG retrieves context before generating an answer.",
    }
    mock_ask.assert_awaited_once_with("What is RAG?")


@patch("app.services.rag_service.ask_agent", new_callable=AsyncMock)
def test_query_data_value_error_returns_400(
    mock_ask: AsyncMock, client: TestClient
) -> None:
    mock_ask.side_effect = ValueError("GOOGLE_API_KEY is not set")

    response = client.post(
        f"{RAG}/query-data",
        json={"question": "What is RAG?"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "GOOGLE_API_KEY is not set"


def test_ingest_data_invalid_url_returns_422(client: TestClient) -> None:
    response = client.post(f"{RAG}/ingest-data", json={"url": "not-a-url"})
    assert response.status_code == 422


def test_query_data_empty_question_returns_422(client: TestClient) -> None:
    response = client.post(f"{RAG}/query-data", json={"question": ""})
    assert response.status_code == 422


@patch("app.services.rag_service.ingestion_pipline", new_callable=AsyncMock)
@patch("app.services.rag_service.ask_agent", new_callable=AsyncMock)
def test_ingest_then_query_flow(
    mock_ask: AsyncMock,
    mock_ingest: AsyncMock,
    client: TestClient,
) -> None:
    mock_ingest.return_value = {
        "url": "https://example.com/rag-post",
        "documents_loaded": 1,
        "chunks_created": 2,
        "chunks_saved": 2,
        "collection": "rag_collection",
    }
    mock_ask.return_value = (
        "Retrieval-Augmented Generation combines search with generation."
    )

    ingest = client.post(
        f"{RAG}/ingest-data",
        json={"url": "https://example.com/rag-post"},
    )
    assert ingest.status_code == 201

    query = client.post(
        f"{RAG}/query-data",
        json={"question": "What is RAG?"},
    )
    assert query.status_code == 200
    assert query.json()["answer"].startswith("Retrieval-Augmented Generation")
