# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Prometheus middleware for HTTP metrics collection."""

import re
import time
from collections.abc import Callable

from django.http import HttpRequest
from django.http.response import HttpResponseBase

from .constants import EXCLUDED_PATHS, PATH_NORMALIZATION_PATTERNS


class PrometheusMiddleware:
    """Middleware to collect HTTP metrics for Prometheus.

    Implements RED methodology:
    - Rate: http_requests_total
    - Errors: http_requests_total with status_code >= 400
    - Duration: http_request_duration_seconds

    Additionally tracks:
    - http_requests_in_progress
    - http_request_size_bytes
    - http_response_size_bytes
    """

    def __init__(
        self, get_response: Callable[[HttpRequest], "HttpResponseBase"]
    ) -> None:
        """Initialize middleware.

        Args:
            get_response: The next middleware or view in the chain.
        """
        self.get_response = get_response
        self._compiled_patterns: list[tuple[re.Pattern[str], str]] = [
            (re.compile(pattern), replacement)
            for pattern, replacement in PATH_NORMALIZATION_PATTERNS
        ]

    def __call__(self, request: HttpRequest) -> "HttpResponseBase":
        """Process the request and collect metrics.

        Args:
            request: The incoming HTTP request.

        Returns:
            The HTTP response from the view.
        """
        path = request.path

        if self._should_exclude(path):
            return self.get_response(request)

        return self._process_request_with_metrics(request, path)

    def _should_exclude(self, path: str) -> bool:  # noqa: PLR6301
        """Check if the path should be excluded from metrics.

        Args:
            path: The request path.

        Returns:
            True if the path should be excluded.
        """
        return any(path.startswith(p) for p in EXCLUDED_PATHS)

    def _normalize_path(self, path: str) -> str:
        """Normalize path to avoid high cardinality.

        Replaces numeric IDs and UUIDs with placeholders.

        Args:
            path: The original request path.

        Returns:
            The normalized path.
        """
        for pattern, replacement in self._compiled_patterns:
            path = pattern.sub(replacement, path)
        return path

    def _process_request_with_metrics(
        self, request: HttpRequest, path: str
    ) -> "HttpResponseBase":
        """Process request and record metrics.

        Args:
            request: The incoming HTTP request.
            path: The request path.

        Returns:
            The HTTP response from the view.
        """
        from .metrics import (  # noqa: PLC0415
            http_exceptions_total,
            http_request_duration_seconds,
            http_request_size_bytes,
            http_requests_in_progress,
            http_requests_total,
            http_response_size_bytes,
        )

        method = request.method or "UNKNOWN"
        endpoint = self._normalize_path(path)

        request_size = self._get_request_size(request)
        http_request_size_bytes.labels(method=method, endpoint=endpoint).observe(
            request_size
        )

        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()

        start_time = time.perf_counter()
        status_code = 500
        response: HttpResponseBase | None = None
        try:
            response = self.get_response(request)
            status_code = getattr(response, "status_code", 500)
        except Exception as e:
            http_exceptions_total.labels(
                endpoint=endpoint,
                exception=e.__class__.__name__,
            ).inc()
            raise
        else:
            return response
        finally:
            duration = time.perf_counter() - start_time

            http_requests_total.labels(
                method=method, endpoint=endpoint, status_code=str(status_code)
            ).inc()
            http_request_duration_seconds.labels(
                method=method, endpoint=endpoint
            ).observe(duration)
            http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()

            if response is not None:
                response_size = self._get_response_size(response)
                http_response_size_bytes.labels(
                    method=method, endpoint=endpoint
                ).observe(response_size)

    def _get_request_size(self, request: HttpRequest) -> int:  # noqa: PLR6301
        """Get the size of the request body in bytes.

        Args:
            request: The HTTP request.

        Returns:
            Size in bytes.
        """
        content_length = request.headers.get("Content-Length")
        if content_length:
            try:
                return int(content_length)
            except ValueError:
                pass
        return 0

    def _get_response_size(self, response: "HttpResponseBase") -> int:  # noqa: PLR6301
        """Get the size of the response body in bytes.

        Args:
            response: The HTTP response.

        Returns:
            Size in bytes.
        """
        content_length = response.get("Content-Length")
        if content_length:
            try:
                return int(content_length)
            except ValueError:
                pass

        content = getattr(response, "content", None)
        if content is not None:
            return len(content)
        return 0
