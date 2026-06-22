"""HTTP client for the FastAPI backend."""

from __future__ import annotations

from typing import Any

import httpx

from config import (
    API_V1_PREFIX,
    AUTH_TIMEOUT_SECONDS,
    INGEST_TIMEOUT_SECONDS,
    QUERY_TIMEOUT_SECONDS,
)


class ApiError(Exception):
    """Raised when the API returns a non-success status."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def _parse_error(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text or f"HTTP {response.status_code}"

    detail = payload.get("detail")
    if isinstance(detail, dict):
        return str(detail.get("message", detail))
    if detail is not None:
        return str(detail)
    return response.text or f"HTTP {response.status_code}"


def _request(
    method: str,
    path: str,
    *,
    token: str | None = None,
    json: dict[str, Any] | None = None,
    timeout: float = AUTH_TIMEOUT_SECONDS,
) -> Any:
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = f"{API_V1_PREFIX}{path}"
    with httpx.Client(timeout=timeout) as client:
        response = client.request(method, url, json=json, headers=headers)

    if response.is_success:
        if response.status_code == 204:
            return None
        return response.json()

    raise ApiError(_parse_error(response), response.status_code)


def signup(email: str, password: str, full_name: str | None) -> dict[str, Any]:
    body: dict[str, Any] = {"email": email, "password": password}
    if full_name:
        body["full_name"] = full_name
    return _request("POST", "/auth/signup", json=body)


def login(email: str, password: str) -> dict[str, Any]:
    return _request("POST", "/auth/login", json={"email": email, "password": password})


def get_me(token: str) -> dict[str, Any]:
    return _request("GET", "/auth/me", token=token)


def ingest_url(url: str, token: str | None = None) -> dict[str, Any]:
    return _request(
        "POST",
        "/rag/ingest-data",
        token=token,
        json={"url": url},
        timeout=INGEST_TIMEOUT_SECONDS,
    )


def query_rag(question: str, token: str | None = None) -> dict[str, Any]:
    return _request(
        "POST",
        "/rag/query-data",
        token=token,
        json={"question": question},
        timeout=QUERY_TIMEOUT_SECONDS,
    )
