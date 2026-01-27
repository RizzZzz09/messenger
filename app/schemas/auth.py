from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    """Схема регистрации пользователя."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    email: EmailStr = Field(
        max_length=255,
        description="Электронная почта",
        examples=["abcd@gmail.com"],
    )
    username: str = Field(
        min_length=3,
        max_length=64,
        description="Имя пользователя",
        examples=["my_username2001"],
    )
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Пароль",
        examples=["my_password123"],
    )


class RegisterResponse(BaseModel):
    """Схема ответа после регистрации с данными пользователя."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    username: str
    created_at: datetime


class LoginRequest(BaseModel):
    """Смеха авторизации пользователя."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    login: str = Field(
        min_length=3,
        max_length=255,
        description="Email или username пользователя",
    )
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Пароль пользователя.",
    )


class LoginResponse(BaseModel):
    """Схема ответа после успешной авторизации пользователя."""

    model_config = ConfigDict(from_attributes=True)

    access_token: str
    token_type: str = "bearer"
