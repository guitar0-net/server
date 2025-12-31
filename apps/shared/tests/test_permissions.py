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
    permission = IsStaffOrReadOnly()
    request = api_request_factory.generic(method, "/")
    drf_request = Request(request)
    drf_request.user = anonymous_user
    view = Mock()

    has_permission = permission.has_permission(drf_request, view)

    assert has_permission is True


@pytest.mark.django_db
@pytest.mark.parametrize("method", ["GET", "HEAD", "OPTIONS"])
def test_safe_methods_allowed_for_common_user(
    api_request_factory: APIRequestFactory,
    common_user: User,
    method: str,
) -> None:
    permission = IsStaffOrReadOnly()
    request = api_request_factory.generic(method, "/")
    drf_request = Request(request)
    drf_request.user = common_user
    view = Mock()

    has_permission = permission.has_permission(drf_request, view)

    assert has_permission is True


@pytest.mark.django_db
@pytest.mark.parametrize("method", ["GET", "HEAD", "OPTIONS"])
def test_safe_methods_allowed_for_staff_user(
    api_request_factory: APIRequestFactory,
    staff_user: User,
    method: str,
) -> None:
    permission = IsStaffOrReadOnly()
    request = api_request_factory.generic(method, "/")
    drf_request = Request(request)
    drf_request.user = staff_user
    view = Mock()

    has_permission = permission.has_permission(drf_request, view)

    assert has_permission is True


@pytest.mark.django_db
@pytest.mark.parametrize("method", ["GET", "HEAD", "OPTIONS"])
def test_safe_methods_allowed_for_super_user(
    api_request_factory: APIRequestFactory,
    superuser: User,
    method: str,
) -> None:
    permission = IsStaffOrReadOnly()
    request = api_request_factory.generic(method, "/")
    drf_request = Request(request)
    drf_request.user = superuser
    view = Mock()

    has_permission = permission.has_permission(drf_request, view)

    assert has_permission is True


@pytest.mark.django_db
@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
def test_unsafe_methods_denied_for_anonymous_user(
    api_request_factory: APIRequestFactory,
    anonymous_user: AnonymousUser,
    method: str,
) -> None:
    permission = IsStaffOrReadOnly()
    request = api_request_factory.generic(method, "/")
    drf_request = Request(request)
    drf_request.user = anonymous_user
    view = Mock()

    has_permission = permission.has_permission(drf_request, view)

    assert has_permission is False


@pytest.mark.django_db
@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
def test_unsafe_methods_denied_for_common_user(
    api_request_factory: APIRequestFactory,
    common_user: User,
    method: str,
) -> None:
    permission = IsStaffOrReadOnly()
    request = api_request_factory.generic(method, "/")
    drf_request = Request(request)
    drf_request.user = common_user
    view = Mock()

    has_permission = permission.has_permission(drf_request, view)

    assert has_permission is False


@pytest.mark.django_db
@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
def test_unsafe_methods_allowed_for_staff_user(
    api_request_factory: APIRequestFactory,
    staff_user: User,
    method: str,
) -> None:
    permission = IsStaffOrReadOnly()
    request = api_request_factory.generic(method, "/")
    drf_request = Request(request)
    drf_request.user = staff_user
    view = Mock()

    has_permission = permission.has_permission(drf_request, view)

    assert has_permission is True


@pytest.mark.django_db
@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
def test_unsafe_methods_allowed_for_super_user(
    api_request_factory: APIRequestFactory,
    superuser: User,
    method: str,
) -> None:
    permission = IsStaffOrReadOnly()
    request = api_request_factory.generic(method, "/")
    drf_request = Request(request)
    drf_request.user = superuser
    view = Mock()

    has_permission = permission.has_permission(drf_request, view)

    assert has_permission is True


@pytest.mark.django_db
def test_permission_check_with_none_user(
    api_request_factory: APIRequestFactory,
) -> None:
    permission = IsStaffOrReadOnly()
    request = api_request_factory.post("/")
    drf_request = Request(request)
    drf_request.user = None  # type: ignore[assignment]
    view = Mock()

    has_permission = permission.has_permission(drf_request, view)

    assert has_permission is False
