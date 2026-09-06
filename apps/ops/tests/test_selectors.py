# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for the ops selectors."""

import pytest
from django.db import DatabaseError, connection

from apps.ops import selectors


@pytest.mark.django_db
def test_is_database_reachable_returns_true_when_query_succeeds() -> None:
    assert selectors.is_database_reachable() is True


@pytest.mark.django_db
def test_is_database_reachable_returns_false_on_database_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_database_error() -> None:
        raise DatabaseError("connection refused")

    monkeypatch.setattr(connection, "cursor", raise_database_error)

    assert selectors.is_database_reachable() is False
