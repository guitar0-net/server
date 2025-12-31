# SPDX-FileCopyrightText: 2025 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Global pytest fixtures ."""

import pytest
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIRequestFactory

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
def common_user(user_factory: type[UserFactory]) -> User:
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
def staff_user(user_factory: type[UserFactory]) -> User:
    """Fixture creating a common user for testing.

    Returns:
        User: A user instance.
    """
    return user_factory.create(
        is_superuser=False,
        is_staff=True,
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


@pytest.fixture
def anonymous_user() -> AnonymousUser:
    """Fixture creating an anonymous user for testing.

    Returns:
        AnonymousUser: An anonymous user instance (not authenticated).
    """
    return AnonymousUser()


@pytest.fixture
def api_request_factory() -> APIRequestFactory:
    """Fixture providing APIRequestFactory for creating mock requests.

    Returns:
        APIRequestFactory instance for creating test requests.
    """
    return APIRequestFactory()
