# SPDX-FileCopyrightText: 2025-2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Views for Prometheus metrics endpoint."""

from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_GET
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from .registry import build_exposition_registry


@require_GET
def metrics_view(request: HttpRequest) -> HttpResponse:
    """Expose Prometheus metrics.

    Args:
        request: The HTTP request.

    Returns:
        HTTP response with Prometheus metrics in text format.
    """
    registry = build_exposition_registry()
    metrics_output = generate_latest(registry)
    response = HttpResponse(
        metrics_output,
        content_type=CONTENT_TYPE_LATEST,
    )
    response["Cache-Control"] = "no-store"
    return response
