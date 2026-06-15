from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import JWTError, jwt  # type: ignore[import]
from pydantic import BaseModel

from app.core.config import get_settings


class TokenPayload(BaseModel):
    """JWT subject payload."""

    sub: str
    exp: datetime | None = None


def hash_password(plain: str) -> str:
    """Hash a password using bcrypt."""
    pwd_bytes = plain.encode("utf-8")
    hashed: bytes = bcrypt.hashpw(pwd_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify plain password against bcrypt hash."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """Encode a JWT access token."""
    settings = get_settings()
    expire = datetime.now(tz=UTC) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode: dict[str, Any] = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> TokenPayload | None:
    """Decode JWT or return None if invalid."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        sub = payload.get("sub")
        if not isinstance(sub, str):
            return None
        return TokenPayload(sub=sub)
    except JWTError:
        return None
