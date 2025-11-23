# SPDX-FileCopyrightText: 2025 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Custom user managers for handing creation with email as primary identifier."""

from typing import Any

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser


class UserManager[UserT: AbstractUser](BaseUserManager[UserT]):
    """Custom user manager where email is the unique identifier for authentication.

    This manager overrides the default to use email instead of username,
    ensuring normalized emails and proper superuser creation.

    Attributes:
        model: The user model this manager is attached to.
    """

    def create_user(
        self,
        email: str,
        password: str | None = None,
        **extra_fields: Any,  # noqa: ANN401
    ) -> UserT:
        """Create and save a regular user with the given email and password.

        Args:
            email (str): User's email address
            password (str | None): User's password (optional)
            extra_fields (Any): Any other fields

        Raises:
            ValueError: If email is not provided.

        Returns:
            UserT: The created user instance
        """
        if not email:
            raise ValueError("The Email field is required")
        email = self.normalize_email(email).lower()
        user: UserT = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        password: str | None,
        **extra_fields: Any,  # noqa: ANN401
    ) -> UserT:
        """Create and save a superuser with the given email and password.

        Args:
            email (str): Superuser's email address (required).
            password (str | None): Superuser's password (required).
            **extra_fields (Any): Additional fields.

        Returns:
            The created superuser instance.

        Raises:
            ValueError: If is_staff or is_superuser are not True, or email is missing.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)
