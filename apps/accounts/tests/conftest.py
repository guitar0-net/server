# SPDX-FileCopyrightText: 2025 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Pytest configuration and fixtures for accounts tests.

This file defines shared fixtures for use across test modules.
"""

import pytest

from apps.accounts.tests.factories.user import UserFactory


@pytest.fixture
def user_factory() -> type[UserFactory]:
    """Fixture providing the UserFactory for creating test users.

    Returns:
        The UserFactory class for declarative user creation.
    """
    return UserFactory
