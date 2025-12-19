# SPDX-FileCopyrightText: 2025 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for custom permissions."""

from unittest.mock import Mock

import pytest
from django.contrib.auth.models import AnonymousUser
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from apps.accounts.models.user import User
from apps.shared.permissions import IsStaffOrReadOnly


@pytest.mark.django_db
@pytest.mark.parametrize("method", ["GET", "HEAD", "OPTIONS"])
def test_safe_methods_allowed_for_anonymous_user(
    api_request_factory: APIRequestFactory,
    anonymous_user: AnonymousUser,
    method: str,
) -> None:
    """Test that safe methods are allowed for anonymous users.

    Args:
        api_request_factory: Factory for creating test requests
        anonymous_user: Anonymous user fixture
        method: HTTP method to test
    """
    # Arrange
    permission = IsStaffOrReadOnly()
    request = api_request_factory.generic(method, "/")
    drf_request = Request(request)
    drf_request.user = anonymous_user
    view = Mock()

    # Act
    has_permission = permission.has_permission(drf_request, view)

    # Assert
    assert has_permission is True


@pytest.mark.django_db
@pytest.mark.parametrize("method", ["GET", "HEAD", "OPTIONS"])
def test_safe_methods_allowed_for_regular_user(
    api_request_factory: APIRequestFactory,
    regular_user: User,
    method: str,
) -> None:
    """Test that safe methods are allowed for regular users.

    Args:
        api_request_factory: Factory for creating test requests
        regular_user: Regular user fixture
        method: HTTP method to test
    """
    # Arrange
    permission = IsStaffOrReadOnly()
    request = api_request_factory.generic(method, "/")
    drf_request = Request(request)
    drf_request.user = regular_user
    view = Mock()

    # Act
    has_permission = permission.has_permission(drf_request, view)

    # Assert
    assert has_permission is True


@pytest.mark.django_db
@pytest.mark.parametrize("method", ["GET", "HEAD", "OPTIONS"])
def test_safe_methods_allowed_for_staff_user(
    api_request_factory: APIRequestFactory,
    staff_user: User,
    method: str,
) -> None:
    """Test that safe methods are allowed for staff users.

    Args:
        api_request_factory: Factory for creating test requests
        staff_user: Staff user fixture
        method: HTTP method to test
    """
    # Arrange
    permission = IsStaffOrReadOnly()
    request = api_request_factory.generic(method, "/")
    drf_request = Request(request)
    drf_request.user = staff_user
    view = Mock()

    # Act
    has_permission = permission.has_permission(drf_request, view)

    # Assert
    assert has_permission is True


@pytest.mark.django_db
@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
def test_unsafe_methods_denied_for_anonymous_user(
    api_request_factory: APIRequestFactory,
    anonymous_user: AnonymousUser,
    method: str,
) -> None:
    """Test that unsafe methods are denied for anonymous users.

    Args:
        api_request_factory: Factory for creating test requests
        anonymous_user: Anonymous user fixture
        method: HTTP method to test
    """
    # Arrange
    permission = IsStaffOrReadOnly()
    request = api_request_factory.generic(method, "/")
    drf_request = Request(request)
    drf_request.user = anonymous_user
    view = Mock()

    # Act
    has_permission = permission.has_permission(drf_request, view)

    # Assert
    assert has_permission is False


@pytest.mark.django_db
@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
def test_unsafe_methods_denied_for_regular_user(
    api_request_factory: APIRequestFactory,
    regular_user: User,
    method: str,
) -> None:
    """Test that unsafe methods are denied for regular users.

    Args:
        api_request_factory: Factory for creating test requests
        regular_user: Regular user fixture
        method: HTTP method to test
    """
    # Arrange
    permission = IsStaffOrReadOnly()
    request = api_request_factory.generic(method, "/")
    drf_request = Request(request)
    drf_request.user = regular_user
    view = Mock()

    # Act
    has_permission = permission.has_permission(drf_request, view)

    # Assert
    assert has_permission is False


@pytest.mark.django_db
@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
def test_unsafe_methods_allowed_for_staff_user(
    api_request_factory: APIRequestFactory,
    staff_user: User,
    method: str,
) -> None:
    """Test that unsafe methods are allowed for staff users.

    Args:
        api_request_factory: Factory for creating test requests
        staff_user: Staff user fixture
        method: HTTP method to test
    """
    # Arrange
    permission = IsStaffOrReadOnly()
    request = api_request_factory.generic(method, "/")
    drf_request = Request(request)
    drf_request.user = staff_user
    view = Mock()

    # Act
    has_permission = permission.has_permission(drf_request, view)

    # Assert
    assert has_permission is True


@pytest.mark.django_db
def test_permission_check_with_none_user(
    api_request_factory: APIRequestFactory,
) -> None:
    """Test permission check when user is None (edge case).

    Args:
        api_request_factory: Factory for creating test requests
    """
    # Arrange
    permission = IsStaffOrReadOnly()
    request = api_request_factory.post("/")
    drf_request = Request(request)
    drf_request.user = None  # type: ignore[assignment]
    view = Mock()

    # Act
    has_permission = permission.has_permission(drf_request, view)

    # Assert
    assert has_permission is False
