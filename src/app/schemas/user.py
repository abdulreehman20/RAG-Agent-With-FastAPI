from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    """Only send fields you want to change. Body must be strict JSON (comma between each property)."""

    full_name: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=128)

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"full_name": "Jane Doe", "password": "newpassword1"},
                {"full_name": "Jane Doe"},
            ],
        },
    )


class UserLogin(BaseModel):
    """Login body — must be strict JSON (no trailing commas after the last field)."""

    email: EmailStr
    password: str

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "email": "user@example.com",
                    "password": "your-password-here",
                },
            ],
        },
    )


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: int | None = None
    email: str | None = None
