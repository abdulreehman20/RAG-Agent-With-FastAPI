from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserRead, UserUpdate
from app.services import user as user_service
from app.db.session import get_session
from app.api.v1.auth import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


# ----------------- List Users Endpoint -----------------
@router.get("/list-users", response_model=list[UserRead])
async def list_users(
    _: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[User]:
    return await user_service.get_all_users(session, skip=skip, limit=limit)


# ----------------- Get User by ID Endpoint -----------------
@router.get("/{user_id}", response_model=UserRead)
async def read_user(
    user_id: int,
    _: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    user = await user_service.get_user_by_id(session, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return user


# ----------------- Update User Endpoint -----------------
@router.put("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    data: UserUpdate,
    _: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    user = await user_service.update_user(session, user_id, data)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return user


# ----------------- Delete User Endpoint -----------------
@router.delete("/{user_id}", response_model=UserRead)
async def delete_user(
    user_id: int,
    _: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    user = await user_service.soft_delete_user(session, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return user
