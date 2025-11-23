# SPDX-FileCopyrightText: 2025 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""App configuration for the Accounts application."""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Configuration class for the Accounts Django app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
