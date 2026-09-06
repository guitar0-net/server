# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Constants for Prometheus metrics configuration."""

METRIC_PREFIX = "guitar0_backend_"

DURATION_BUCKETS: tuple[float, ...] = (
    0.005,
    0.01,
    0.025,
    0.05,
    0.075,
    0.1,
    0.25,
    0.5,
    0.75,
    1.0,
    2.5,
    5.0,
    7.5,
    10.0,
    15.0,
    30.0,
)

SIZE_BUCKETS_BYTES: tuple[float, ...] = (
    100,
    500,
    1000,  # 1KB
    5000,
    10000,  # 10KB
    50000,
    100000,  # 100KB
    500000,
    1000000,  # 1MB
    5000000,
    10000000,  # 10MB
    50000000,
    100000000,  # 100MB
)

EXCLUDED_PATHS: frozenset[str] = frozenset({
    "/metrics/",
    "/health/",
    "/ready/",
})


_UUID_PATTERN = (
    r"/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}/?"
)
PATH_NORMALIZATION_PATTERNS: tuple[tuple[str, str], ...] = (
    (_UUID_PATTERN, "/{uuid}/"),
    (r"/\d+/?", "/{id}/"),
)
