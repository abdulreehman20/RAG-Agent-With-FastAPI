from __future__ import annotations

from functools import lru_cache
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(
        ...,
        validation_alias=AliasChoices("DATABASE_URL", "database_url"),
        description="Async SQLAlchemy URL, e.g. postgresql+asyncpg://...",
    )

    secret_key: str = Field(
        ..., validation_alias=AliasChoices("SECRET_KEY", "secret_key")
    )
    algorithm: str = Field(
        default="HS256", validation_alias=AliasChoices("ALGORITHM", "algorithm")
    )
    access_token_expire_minutes: int = Field(
        default=60,
        ge=1,
        validation_alias=AliasChoices(
            "ACCESS_TOKEN_EXPIRE_MINUTES", "access_token_expire_minutes"
        ),
    )


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()


# print(get_settings())