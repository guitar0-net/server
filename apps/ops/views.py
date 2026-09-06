# SPDX-FileCopyrightText: 2025-2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Views for the operational endpoints: metrics, liveness and readiness."""

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.http import require_GET
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from .registry import build_exposition_registry
from .selectors import is_database_reachable


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


@require_GET
def health_view(request: HttpRequest) -> HttpResponse:
    """Report that the process is alive, without touching any dependency.

    Drives the container healthcheck, so it deliberately checks nothing
    external: a database blip must not restart a process that still serves
    traffic.

    Args:
        request: The HTTP request.

    Returns:
        HTTP 200 for as long as the worker can answer at all.
    """
    response = JsonResponse({"status": "ok"})
    response["Cache-Control"] = "no-store"
    return response


@require_GET
def ready_view(request: HttpRequest) -> HttpResponse:
    """Report whether the app can serve requests that need the database.

    Gates the deploy and the rollback, which poll it until it answers 200 —
    so a container that boots but cannot reach Postgres fails the rollout
    instead of passing it.

    Args:
        request: The HTTP request.

    Returns:
        HTTP 200 when the database answers, HTTP 503 otherwise.
    """
    database_reachable = is_database_reachable()
    response = JsonResponse(
        {
            "status": "ready" if database_reachable else "not ready",
            "database": database_reachable,
        },
        status=200 if database_reachable else 503,
    )
    response["Cache-Control"] = "no-store"
    return response
