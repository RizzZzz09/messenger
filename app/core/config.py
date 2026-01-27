from datetime import timedelta
from pathlib import Path
from typing import List, Literal

from authx import AuthXConfig
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    """Конфигурация приложения, загружаемая из переменных окружения."""

    database_url: str = Field(default=...)

    # JWT
    JWT_SECRET_KEY: str = Field(default=...)
    JWT_ALGORITHM: Literal["HS256", "HS384", "HS512", "RS256", "RS384", "RS512"] = Field(
        default=...
    )
    JWT_TOKEN_LOCATION: List[Literal["headers", "cookies", "json", "query"]] = Field(default=...)
    JWT_ACCESS_TOKEN_EXPIRES: int = Field(default=...)
    JWT_REFRESH_TOKEN_EXPIRES: int = Field(default=...)
    JWT_REFRESH_COOKIE_NAME: str = Field(default=...)
    JWT_COOKIE_SECURE: bool = Field(default=...)

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()

auth_config = AuthXConfig(
    JWT_SECRET_KEY=settings.JWT_SECRET_KEY,
    JWT_ALGORITHM=settings.JWT_ALGORITHM,
    JWT_TOKEN_LOCATION=settings.JWT_TOKEN_LOCATION,
    JWT_ACCESS_TOKEN_EXPIRES=timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRES),
    JWT_REFRESH_TOKEN_EXPIRES=timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRES),
    JWT_REFRESH_COOKIE_NAME=settings.JWT_REFRESH_COOKIE_NAME,
    JWT_COOKIE_SECURE=settings.JWT_COOKIE_SECURE,
)
