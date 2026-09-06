# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Pytest configuration and fixtures for metrics tests."""

import importlib
from collections.abc import Generator

import pytest


@pytest.fixture
def fresh_registry() -> Generator[None]:
    """Provide a fresh metrics registry for a single test.

    This fixture resets the registry before the test and reloads the metrics
    module to re-register all metrics. Use this fixture explicitly when you
    need test isolation for registry-related tests.
    """
    from apps.ops import metrics as metrics_module
    from apps.ops import registry

    registry.reset_registry()
    importlib.reload(metrics_module)
    yield
    registry.reset_registry()
    importlib.reload(metrics_module)
