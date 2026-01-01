# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""App configuration for the schemes application."""

from django.apps import AppConfig


class SchemesConfig(AppConfig):
    """Configuration class for the schemes Django app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.schemes"
