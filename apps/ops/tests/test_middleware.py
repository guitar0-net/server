# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for the Prometheus middleware."""

import pytest
from django.http import HttpRequest, HttpResponse, StreamingHttpResponse
from django.test import RequestFactory

from apps.ops.middleware import PrometheusMiddleware


@pytest.fixture
def request_factory() -> RequestFactory:
    return RequestFactory()


@pytest.fixture
def middleware() -> PrometheusMiddleware:
    def get_response(request: HttpRequest) -> HttpResponse:
        return HttpResponse("OK", status=200)

    return PrometheusMiddleware(get_response)


def test_middleware_returns_response(
    middleware: PrometheusMiddleware, request_factory: RequestFactory
) -> None:
    request = request_factory.get("/api/test/")
    response = middleware(request)
    assert response.status_code == 200


def test_middleware_excludes_metrics_path(
    middleware: PrometheusMiddleware, request_factory: RequestFactory
) -> None:
    request = request_factory.get("/metrics/")
    response = middleware(request)
    assert response.status_code == 200


def test_path_normalization_normalizes_numeric_ids(
    middleware: PrometheusMiddleware,
) -> None:
    path = "/api/chords/123/"
    normalized = middleware._normalize_path(path)
    assert normalized == "/api/chords/{id}/"


def test_path_normalization_normalizes_uuids(
    middleware: PrometheusMiddleware,
) -> None:
    path = "/api/chords/550e8400-e29b-41d4-a716-446655440000/"
    normalized = middleware._normalize_path(path)
    assert normalized == "/api/chords/{uuid}/"


def test_path_normalization_preserves_non_id_paths(
    middleware: PrometheusMiddleware,
) -> None:
    path = "/api/chords/"
    normalized = middleware._normalize_path(path)
    assert normalized == "/api/chords/"


def test_metrics_recording_increments_request_counter(
    middleware: PrometheusMiddleware, request_factory: RequestFactory
) -> None:
    from apps.ops.metrics import http_requests_total

    request = request_factory.get("/api/test/")
    middleware(request)

    sample_value = http_requests_total.labels(
        method="GET", endpoint="/api/test/", status_code="200"
    )._value.get()

    assert sample_value >= 1


def test_metrics_recording_records_duration(
    middleware: PrometheusMiddleware, request_factory: RequestFactory
) -> None:
    from apps.ops.registry import get_registry

    request = request_factory.get("/api/duration/")
    middleware(request)

    registry = get_registry()
    samples = list(registry.collect())

    for metric_family in samples:
        if metric_family.name == "guitar0_backend_http_request_duration_seconds":
            for sample in metric_family.samples:
                if sample.labels.get("endpoint") == "/api/duration/":
                    assert True
                    return
    pytest.fail("No duration samples found for /api/duration/")


def test_metrics_recording_tracks_in_progress_requests(
    middleware: PrometheusMiddleware, request_factory: RequestFactory
) -> None:
    from apps.ops.metrics import http_requests_in_progress

    initial_value = http_requests_in_progress.labels(
        method="GET", endpoint="/api/progress/"
    )._value.get()

    request = request_factory.get("/api/progress/")
    middleware(request)

    final_value = http_requests_in_progress.labels(
        method="GET", endpoint="/api/progress/"
    )._value.get()

    assert final_value == initial_value


def test_request_size_records_from_header(request_factory: RequestFactory) -> None:
    def get_response(request: HttpRequest) -> HttpResponse:
        return HttpResponse("OK")

    middleware = PrometheusMiddleware(get_response)
    request = request_factory.post(
        "/api/data/",
        data="test data",
        content_type="text/plain",
    )
    request.META["CONTENT_LENGTH"] = "100"

    size = middleware._get_request_size(request)
    assert size == 100


def test_request_size_returns_zero_for_missing_content_length(
    request_factory: RequestFactory,
) -> None:
    def get_response(request: HttpRequest) -> HttpResponse:
        return HttpResponse("OK")

    middleware = PrometheusMiddleware(get_response)
    request = request_factory.get("/api/data/")
    if "CONTENT_LENGTH" in request.META:
        del request.META["CONTENT_LENGTH"]

    size = middleware._get_request_size(request)
    assert size == 0


def test_request_size_returns_zero_for_invalid_content_length(
    request_factory: RequestFactory,
) -> None:
    def get_response(request: HttpRequest) -> HttpResponse:
        return HttpResponse("OK")

    middleware = PrometheusMiddleware(get_response)
    request = request_factory.post("/api/data/", content_type="text/plain")
    request.META["CONTENT_LENGTH"] = "invalid"

    size = middleware._get_request_size(request)
    assert size == 0


def test_response_size_records_from_content() -> None:
    def get_response(request: HttpRequest) -> HttpResponse:
        return HttpResponse("Hello World")

    middleware = PrometheusMiddleware(get_response)
    response = HttpResponse("Hello World")

    size = middleware._get_response_size(response)
    assert size == len(b"Hello World")


def test_response_size_records_from_header() -> None:
    def get_response(request: HttpRequest) -> HttpResponse:
        return HttpResponse("OK")

    middleware = PrometheusMiddleware(get_response)
    response = HttpResponse("x" * 1000)
    response["Content-Length"] = "500"

    size = middleware._get_response_size(response)
    assert size == 500


def test_response_size_returns_zero_for_invalid_content_length_header() -> None:
    def get_response(request: HttpRequest) -> HttpResponse:
        return HttpResponse("OK")

    middleware = PrometheusMiddleware(get_response)
    response = StreamingHttpResponse(iter([b"chunk"]))
    response["Content-Length"] = "invalid"

    size = middleware._get_response_size(response)
    assert size == 0


def test_response_size_returns_zero_for_response_without_content() -> None:
    def get_response(request: HttpRequest) -> HttpResponse:
        return HttpResponse("OK")

    middleware = PrometheusMiddleware(get_response)
    response = StreamingHttpResponse(iter([b"chunk"]))

    size = middleware._get_response_size(response)
    assert size == 0


def test_exception_handling_records_exception_metric(
    request_factory: RequestFactory,
) -> None:
    from apps.ops.metrics import http_exceptions_total

    class CustomError(Exception):
        pass

    def get_response(request: HttpRequest) -> HttpResponse:
        raise CustomError("Something went wrong")

    middleware = PrometheusMiddleware(get_response)
    request = request_factory.get("/api/error/")

    with pytest.raises(CustomError):
        middleware(request)

    sample_value = http_exceptions_total.labels(
        endpoint="/api/error/",
        exception="CustomError",
    )._value.get()

    assert sample_value >= 1
