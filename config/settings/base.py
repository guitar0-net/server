# SPDX-FileCopyrightText: 2025 Andrey Kotlyar
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Django configuration with typing."""

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
    """Base configuration class.

    Inherits from `pydantic_settings.BaseSettings` to automatically
    load values from environment variables.

    Args:
        BaseSettings (class): Parent class that provides functionality
            for working with environment variables.
    """

    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    LOG_FILE_PATH: Path = BASE_DIR / "logs" / "django.log"
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
    """Retrieve the project settings.

    Uses caching to ensure that the settings class is loaded only once
    during the application's lifetime.

    Returns:
        Settings: The base configuration class for the project.
    """
    return Settings()  # pyright: ignore[reportCallIssue]
