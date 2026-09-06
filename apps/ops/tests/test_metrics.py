# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for the HTTP metrics definitions."""

from prometheus_client import REGISTRY

from apps.ops.constants import (
    DURATION_BUCKETS,
    METRIC_PREFIX,
    SIZE_BUCKETS_BYTES,
)
from apps.ops.registry import get_registry


def test_duration_buckets_cover_reasonable_range() -> None:
    assert min(DURATION_BUCKETS) >= 0.001
    assert max(DURATION_BUCKETS) <= 60


def test_size_buckets_cover_reasonable_range() -> None:
    assert min(SIZE_BUCKETS_BYTES) >= 1
    assert max(SIZE_BUCKETS_BYTES) <= 1_000_000_000


def test_metrics_not_in_default_registry() -> None:
    """Ensure our metrics use custom registry, not the default one."""
    registry = get_registry()
    assert registry is not REGISTRY

    metric_names = [m.name for m in registry.collect()]
    assert f"{METRIC_PREFIX}http_requests" in metric_names
