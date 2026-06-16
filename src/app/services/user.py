from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import hash_password, verify_password


async def create_user(session: AsyncSession, data: UserCreate) -> User:
    """Create a new active user with hashed password."""

    user = User(
        email=data.email.lower().strip(),
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        is_active=True,
    )

    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    """Fetch a user by ID."""

    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


def _utc_now_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


async def get_all_users(
    session: AsyncSession, *, skip: int = 0, limit: int = 50
) -> list[User]:
    """Paginated list of users ordered by id."""

    stmt = select(User).order_by(col(User.id)).offset(skip).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def update_user(
    session: AsyncSession, user_id: int, data: UserUpdate
) -> User | None:
    """Update full_name and/or password; returns None if user missing."""

    user = await get_user_by_id(session, user_id)
    if user is None:
        return None
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.password is not None:
        user.hashed_password = hash_password(data.password)
    user.updated_at = _utc_now_naive()
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def soft_delete_user(session: AsyncSession, user_id: int) -> User | None:
    """Set is_active=False; returns None if user missing."""

    user = await get_user_by_id(session, user_id)
    if user is None:
        return None
    user.is_active = False
    user.updated_at = _utc_now_naive()
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """Fetch a user by email (case-insensitive)."""

    stmt = select(User).where(User.email == email.lower().strip())
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def authenticate_user(
    session: AsyncSession, email: str, password: str
) -> User | None:
    """Verify email and password, return user if valid."""

    user = await get_user_by_email(session, email)
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
