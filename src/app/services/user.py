from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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

    stmt = select(User).filter_by(id=user_id)  # Fix this is their any error occur
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


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
