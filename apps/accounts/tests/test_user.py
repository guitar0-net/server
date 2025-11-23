# SPDX-FileCopyrightText: 2025 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for User."""

import pytest
from django.contrib.auth import get_user_model

from apps.accounts.models.user import User
from apps.accounts.tests.factories.user import UserFactory


@pytest.mark.django_db
def test_user_model_configuration(user_factory: type[UserFactory]) -> None:
    user = user_factory()
    assert get_user_model() == User
    assert User.USERNAME_FIELD == "email"
    assert User.REQUIRED_FIELDS == []
    assert isinstance(user.email, str)


@pytest.mark.django_db
def test_user_str_representation(user_factory: type[UserFactory]) -> None:
    user = user_factory(email="user@example.com")
    assert str(user) == "user@example.com"
