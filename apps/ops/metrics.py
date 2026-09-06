# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""HTTP metrics for Prometheus monitoring (RED methodology)."""

from prometheus_client import Counter, Gauge, Histogram

from .constants import DURATION_BUCKETS, METRIC_PREFIX, SIZE_BUCKETS_BYTES
from .registry import get_registry

# HTTP request metrics

http_requests_total = Counter(
    name=f"{METRIC_PREFIX}http_requests_total",
    documentation="Total number of HTTP requests.",
    labelnames=["method", "endpoint", "status_code"],
    registry=get_registry(),
)

http_request_duration_seconds = Histogram(
    name=f"{METRIC_PREFIX}http_request_duration_seconds",
    documentation="HTTP request duration in seconds.",
    labelnames=["method", "endpoint"],
    buckets=DURATION_BUCKETS,
    registry=get_registry(),
)

http_requests_in_progress = Gauge(
    name=f"{METRIC_PREFIX}http_requests_in_progress",
    documentation="Number of HTTP requests currently in progress.",
    labelnames=["method", "endpoint"],
    registry=get_registry(),
    multiprocess_mode="livesum",
)

http_exceptions_total = Counter(
    name=f"{METRIC_PREFIX}http_exceptions_total",
    documentation="Unhandled exceptions during HTTP request processing.",
    labelnames=["endpoint", "exception"],
    registry=get_registry(),
)

http_request_size_bytes = Histogram(
    name=f"{METRIC_PREFIX}http_request_size_bytes",
    documentation="HTTP request size in bytes.",
    labelnames=["method", "endpoint"],
    buckets=SIZE_BUCKETS_BYTES,
    registry=get_registry(),
)

http_response_size_bytes = Histogram(
    name=f"{METRIC_PREFIX}http_response_size_bytes",
    documentation="HTTP response size in bytes.",
    labelnames=["method", "endpoint"],
    buckets=SIZE_BUCKETS_BYTES,
    registry=get_registry(),
)

# Application info metrics

app_info = Gauge(
    name=f"{METRIC_PREFIX}app_info",
    documentation="Application information.",
    labelnames=["version", "git_sha", "build_datetime"],
    registry=get_registry(),
    multiprocess_mode="max",
)

app_startup_timestamp_seconds = Gauge(
    name=f"{METRIC_PREFIX}app_startup_timestamp_seconds",
    documentation="Application startup time (unix timestamp).",
    registry=get_registry(),
    multiprocess_mode="max",
)
