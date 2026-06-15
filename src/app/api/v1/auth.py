from __future__ import annotations

import logging

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.db.session import get_session
from app.services import user as user_service
from app.core.http_errors import error_detail
from app.core.security import create_access_token, decode_access_token
from app.schemas.user import Token, UserCreate, UserLogin, UserRead

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)


# ----------------- Get Current User Dependency -----------------
async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    """Resolve the current user from a Bearer JWT."""

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_detail(
                "No access token was sent. Log in with POST /api/v1/auth/login, copy "
                "`access_token`, then in Swagger click **Authorize** → HTTP Bearer and paste the token.",
                "AUTH_REQUIRED",
            ),
            headers={"WWW-Authenticate": 'Bearer realm="api"'},
        )

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_detail(
                'Authorization must use the Bearer scheme (header: Authorization: Bearer <token>).',
                "AUTH_INVALID_SCHEME",
            ),
            headers={"WWW-Authenticate": 'Bearer realm="api"'},
        )

    payload = decode_access_token(credentials.credentials)

    if payload is None or not payload.sub.isdigit():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_detail(
                "The access token is missing, invalid, or expired. Log in again to obtain a new token.",
                "TOKEN_INVALID",
            ),
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        )

    user = await user_service.get_user_by_id(session, int(payload.sub))

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_detail(
                "No user matches this token. The account may have been removed.",
                "USER_NOT_FOUND",
            ),
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_detail(
                "This account is deactivated. Contact support if you believe this is a mistake.",
                "USER_INACTIVE",
            ),
        )

    return user


# ----------------- Signup Endpoint -----------------
@router.post("/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def signup(
    data: UserCreate, session: Annotated[AsyncSession, Depends(get_session)]
) -> User:
    existing = await user_service.get_user_by_email(session, data.email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_detail(
                "An account with this email already exists. Try logging in or use a different email.",
                "EMAIL_ALREADY_REGISTERED",
            ),
        )
    try:
        return await user_service.create_user(session, data)
    except Exception:
        logger.exception("signup failed")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_detail(
                "Registration could not be completed. Please try again later.",
                "SIGNUP_FAILED",
            ),
        ) from None


# ----------------- Login Endpoint -----------------
@router.post("/login", response_model=Token)
async def login(
    data: UserLogin, session: Annotated[AsyncSession, Depends(get_session)]
) -> Token:
    user = await user_service.authenticate_user(session, data.email, data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_detail(
                "Email or password is incorrect, or the account is inactive.",
                "INVALID_CREDENTIALS",
            ),
            headers={"WWW-Authenticate": 'Bearer realm="api"'},
        )
    token = create_access_token(subject=str(user.id))
    return Token(access_token=token)


# ----------------- Me Endpoint -----------------
@router.get(
    "/me",
    response_model=UserRead,
    summary="Current user profile",
    description=(
        "**Requires authentication.** First call **POST /api/v1/auth/login**, copy "
        "`access_token` from the response, then click the green **Authorize** button "
        "at the top of Swagger, choose **HTTP Bearer**, and paste the token."
    ),
)
async def read_me(current: Annotated[User, Depends(get_current_user)]) -> User:
    return current
