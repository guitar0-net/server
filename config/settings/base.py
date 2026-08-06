# SPDX-FileCopyrightText: 2025-2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Django configuration with typing."""

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal, TypedDict

from pydantic_settings import BaseSettings, SettingsConfigDict

_env = os.environ.get("ENVIRONMENT", "development")


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
    VERSION: str = "unknown"
    GIT_SHA: str = "unknown"
    BUILD_DATETIME: str = "unknown"

    SECRET_KEY: str
    DATABASE_URL: str
    GOOGLE_CLIENT_ID: str | None = None

    GOOGLE_PLAY_PACKAGE_NAME: str | None = None
    GOOGLE_PLAY_SERVICE_ACCOUNT_INFO: str | None = None

    APPLE_BUNDLE_ID: str | None = None
    # App Store Connect's numeric app id, required to verify a signed
    # transaction was issued for *this* app once the client is talking about
    # the Production environment.
    APPLE_APP_APPLE_ID: int | None = None

    DEBUG: bool = False
    ALLOWED_HOSTS: list[str] = []
    CSRF_TRUSTED_ORIGINS: list[str] = []

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
        env_file=".env.development" if _env == "development" else None,
        env_file_encoding="utf-8",
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
