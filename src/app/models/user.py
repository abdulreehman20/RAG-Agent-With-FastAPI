from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def _utc_now_naive() -> datetime:
    """UTC instant as naive datetime — matches PostgreSQL TIMESTAMP WITHOUT TIME ZONE."""
    return datetime.now(UTC).replace(tzinfo=None)


class User(SQLModel, table=True):
    """Application user (soft-delete via is_active)."""

    __tablename__ = "user"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True, max_length=320)
    hashed_password: str = Field(max_length=255)
    full_name: str | None = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=_utc_now_naive)
    updated_at: datetime = Field(default_factory=_utc_now_naive)
