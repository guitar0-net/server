# SPDX-FileCopyrightText: 2025 Andrey Kotlyar
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Logging configuration for the Django project.

This module defines the centralized logging setup used across the application.
It includes handlers, formatters, filters, and loggers configuration.

The configuration ensures that:
- Logs are written both to the console (for development) and to rotating files.
- Sensitive information is filtered out before being written to logs.
- Critical errors are automatically emailed to administrators in production.

Functions:
    get_logging_config(settings: Settings) -> LoggingConfig:
        Returns the full logging configuration dictionary for Django.
"""

from typing import Literal, TypedDict

from .base import Settings

type DebugLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class _Formatter(TypedDict):
    format: str
    style: str


_Filter = TypedDict("_Filter", {"()": str})


_Handler = TypedDict(
    "_Handler",
    {
        "level": DebugLevel,
        "class": str,
        "formatter": str,
        "filename": str | None,
        "maxBytes": int | None,
        "backupCount": int | None,
        "filters": list[str] | None,
    },
    total=False,
)


class _Logger(TypedDict):
    handlers: list[str]
    level: DebugLevel
    propagate: bool


class LoggingConfig(TypedDict):
    """TypedDict defining the structure of the Django logging configuration.

    Specifies the expected keys and value types for handlers, formatters,
    filters, and loggers used in the application's logging system.
    """

    version: int
    disable_existing_loggers: bool
    formatters: dict[str, _Formatter]
    filters: dict[str, _Filter]
    handlers: dict[str, _Handler]
    loggers: dict[str, _Logger]


def get_logging_config(settings: Settings) -> LoggingConfig:
    """Return the logging configuration dictionary for Django.

    Builds and returns a structured logging configuration based on
    project settings.

    Args:
        settings (Settings): The project settings instance.

    Returns:
        LoggingConfig: The complete Django logging configuration dictionary.
    """
    base_logging: LoggingConfig = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {
                "format": "{levelname} {message}",
                "style": "{",
            },
            "verbose": {
                "format": "{asctime} {levelname} {module}"
                "{process:d} {thread:d} {message}",
                "style": "{",
            },
        },
        "filters": {
            "require_debug_false": {
                "()": "django.utils.log.RequireDebugFalse",
            },
            "sensitive_data_filter": {
                "()": "config.settings.filters.SensitiveDataFilter",
            },
        },
        "handlers": {
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "simple",
            },
            "file": {
                "level": "INFO",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": str(settings.LOG_FILE_PATH),
                "maxBytes": 1024 * 1024 * 5,
                "backupCount": 5,
                "formatter": "verbose",
                "filters": ["sensitive_data_filter"],
            },
            "mail_admins": {
                "level": "ERROR",
                "class": "django.utils.log.AdminEmailHandler",
                "filters": ["require_debug_false"],
            },
        },
        "loggers": {
            "": {
                "handlers": ["console", "file"],
                "level": "WARNING",
                "propagate": False,
            },
            "django": {
                "handlers": ["console", "file", "mail_admins"],
                "level": "INFO",
                "propagate": False,
            },
            "rest_framework": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
            "accounts": {
                "handlers": ["console", "file"],
                "level": "DEBUG" if settings.DEBUG else "INFO",
                "propagate": False,
            },
        },
    }
    return base_logging
