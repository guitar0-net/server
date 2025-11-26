# SPDX-FileCopyrightText: 2025 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Pytest configuration and fixtures for accounts tests.

This file defines shared fixtures for use across test modules.
"""

import pytest

from apps.accounts.models.user import User
from apps.accounts.tests.factories.user import UserFactory


@pytest.fixture
def user_factory() -> type[UserFactory]:
    """Fixture providing the UserFactory for creating test users.

    Returns:
        The UserFactory class for declarative user creation.
    """
    return UserFactory


@pytest.fixture
def user(user_factory: type[UserFactory]) -> User:
    """Fixture creating a common user for testing.

    Returns:
        User: A user instance.
    """
    return user_factory.create(
        is_superuser=False,
        is_staff=False,
        password="password",
    )


@pytest.fixture
def superuser(user_factory: type[UserFactory]) -> User:
    """Fixture creating a superuser for testing.

    Returns:
        User: A superuser instance.
    """
    return user_factory.create(
        is_superuser=True,
        is_staff=True,
        email="admin@example.com",
        password="password123",
    )
