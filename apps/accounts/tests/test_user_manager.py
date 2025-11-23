# SPDX-FileCopyrightText: 2025 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for UserManager."""

import pytest

from apps.accounts.models.user import User


@pytest.mark.django_db
def test_create_user_success() -> None:
    user = User.objects.create_user(
        "  EXAMPLE@Email.COM  ",
        "secret-password",
        first_name="John",
    )

    assert isinstance(user, User)
    assert user.email == "example@email.com"
    assert user.check_password("secret-password")
    assert user.first_name == "John"
    assert user.username is None
    assert user.is_active
    assert not user.is_staff
    assert not user.is_superuser


@pytest.mark.django_db
def test_create_user_without_password() -> None:
    user = User.objects.create_user("email")

    assert not user.has_usable_password()


@pytest.mark.django_db
def test_create_user_no_email_raises() -> None:
    with pytest.raises(ValueError, match="The Email field is required"):
        User.objects.create_user(None)  # type: ignore[arg-type]


@pytest.mark.django_db
def test_create_superuser_success() -> None:
    user = User.objects.create_superuser(
        "example@email.com", "super-secret-password", first_name="Bob"
    )

    assert isinstance(user, User)
    assert user.email == "example@email.com"
    assert user.check_password("super-secret-password")
    assert user.first_name == "Bob"
    assert user.username is None
    assert user.is_active
    assert user.is_staff is True
    assert user.is_superuser is True


def test_create_superuser_no_is_staff_raise() -> None:
    with pytest.raises(ValueError):
        User.objects.create_superuser("admin@example.com", "pass", is_staff=False)


def test_create_superuser_no_is_superuser_raise() -> None:
    with pytest.raises(ValueError):
        User.objects.create_superuser("admin@example.com", "pass", is_superuser=False)
