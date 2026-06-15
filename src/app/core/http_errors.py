"""Structured HTTP error bodies: ``{"detail": {"message": "...", "code": "..."}}``."""

from __future__ import annotations


def error_detail(message: str, code: str) -> dict[str, str]:
    """Build a consistent ``detail`` payload for ``HTTPException``."""
    return {"message": message, "code": code}
