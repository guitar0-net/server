from functools import lru_cache
from pathlib import Path
from typing import Literal, TypedDict

from pydantic_settings import BaseSettings, SettingsConfigDict


class _TemplateBackend(TypedDict):
    BACKEND: str
    DIRS: list[Path]
    APP_DIRS: bool
    OPTIONS: dict[str, object]


class Settings(BaseSettings):
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    SECRET_KEY: str
    DATABASE_URL: str

    DEBUG: bool = False
    ALLOWED_HOSTS: list[str] = []

    TEMPLATES: list[_TemplateBackend] = [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [BASE_DIR / "templates"],
            "APP_DIRS": True,
            "OPTIONS": {
                "context_processors": [
                    "django.template.context_processors.debug",
                    "django.template.context_processors.request",
                    "django.contrib.auth.context_processors.auth",
                    "django.contrib.messages.context_processors.messages",
                ],
            },
        }
    ]

    model_config = SettingsConfigDict(
        env_file=f".env.{ENVIRONMENT}",
        env_file_encoding="utf-8",
        secrets_dir="/run/secrets",
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # pyright: ignore[reportCallIssue]
