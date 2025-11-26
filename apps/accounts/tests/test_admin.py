# SPDX-FileCopyrightText: 2025 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for the admin interface of users' accounts."""

import pytest
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory
from django.urls import reverse

from apps.accounts.admin import UserAdmin
from apps.accounts.models.user import User


@pytest.fixture
def admin_site() -> admin.AdminSite:
    return admin.site


@pytest.fixture
def user_admin(admin_site: admin.AdminSite) -> UserAdmin:
    return UserAdmin(User, admin_site)


def test_list_display_configuration(user_admin: UserAdmin) -> None:
    expected = ("id", "email", "is_active", "is_staff", "is_superuser", "date_joined")
    assert user_admin.list_display == expected


def test_search_fields_configuration(user_admin: UserAdmin) -> None:
    expected = ("email",)
    assert user_admin.search_fields == expected


def test_fieldsets_configuration(user_admin: UserAdmin) -> None:
    expected = (
        (None, {"fields": ("email", "password")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    assert user_admin.fieldsets == expected


def test_add_fieldsets_configuration(user_admin: UserAdmin) -> None:
    expected = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "is_active", "is_staff"),
            },
        ),
    )
    assert user_admin.add_fieldsets == expected


@pytest.mark.django_db
def test_model_registration(admin_site: admin.AdminSite) -> None:
    assert isinstance(admin_site._registry[User], UserAdmin)


@pytest.mark.django_db
def test_admin_list_view_access_user(
    user: User,
) -> None:
    factory = RequestFactory()
    request = factory.get(reverse("admin:accounts_user_changelist"))
    request.user = user
    with pytest.raises(PermissionDenied):
        _ = UserAdmin(User, admin.site).changelist_view(request)


@pytest.mark.django_db
def test_admin_list_view_access_superuser(
    superuser: User,
) -> None:
    factory = RequestFactory()
    request = factory.get(reverse("admin:accounts_user_changelist"))
    request.user = superuser
    response = UserAdmin(User, admin.site).changelist_view(request)
    assert response.status_code == HttpResponse.status_code
