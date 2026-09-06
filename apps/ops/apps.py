# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""App configuration for the ops application."""

import time

from django.apps import AppConfig
from django.conf import settings


class OpsConfig(AppConfig):
    """Configuration class for the ops Django app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ops"
    verbose_name = "Operations"

    def ready(self) -> None:  # noqa: PLR6301
        """Initialize metrics when the app is ready.

        This method is called when Django starts and ensures that all metrics
        are registered early in the application lifecycle.
        """
        from . import metrics  # noqa: PLC0415

        version = getattr(settings, "VERSION", "unknown")
        git_sha = getattr(settings, "GIT_SHA", "unknown")
        build_datetime = getattr(settings, "BUILD_DATETIME", "unknown")
        metrics.app_info.labels(
            version=version,
            git_sha=git_sha,
            build_datetime=build_datetime,
        ).set(1)
        metrics.app_startup_timestamp_seconds.set(time.time())
