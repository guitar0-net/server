# SPDX-FileCopyrightText: 2025 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""User models module."""

from typing import ClassVar

from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.accounts.managers.user_manager import UserManager


class User(AbstractUser):
    """Main user class for authentication and profiles.

    This model extends Django's AbstractUser to use email as the primary
    identifier instead of username, which is disabled via `username = None`.
    Type ignores are used for mypy compatibility with django-stubs, as overriding
    built-in fields to None is runtime-safe but statically flagged.

    Attributes:
        email: Unique email field used as the username for authentication.
    """

    username = None  # type: ignore[assignment]

    email = models.EmailField("Email", unique=True)

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS: ClassVar[list[str]] = []

    objects = UserManager["User"]()  # type: ignore[misc, assignment]
