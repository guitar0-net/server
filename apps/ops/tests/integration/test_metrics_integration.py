# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Integration tests for the ops application."""

import pytest
from django.test import Client


@pytest.mark.integration
@pytest.mark.django_db
def test_full_metrics_flow(client: Client) -> None:
    """Test that making requests results in metrics being recorded."""
    client.get("/api/v1/data/chords/")
    client.get("/api/v1/data/chords/")
    client.get("/admin/")

    response = client.get("/metrics/")
    content = response.content.decode("utf-8")

    assert "guitar0_backend_http_requests_total" in content
    assert "guitar0_backend_http_request_duration_seconds" in content
    assert "guitar0_backend_http_requests_in_progress" in content
    assert "guitar0_backend_http_exceptions_total" in content
    assert "guitar0_backend_app_info" in content


@pytest.mark.integration
@pytest.mark.django_db
def test_metrics_endpoint_not_counted(client: Client) -> None:
    """Verify that /metrics/ requests are not counted in metrics."""
    client.get("/metrics/")

    for _ in range(5):
        client.get("/metrics/")

    response = client.get("/metrics/")
    final_content = response.content.decode("utf-8")

    assert 'endpoint="/metrics/"' not in final_content


@pytest.mark.integration
@pytest.mark.django_db
def test_path_normalization_in_metrics(client: Client) -> None:
    """Test that numeric IDs are normalized in metrics labels."""
    client.get("/api/v1/data/chords/1/")
    client.get("/api/v1/data/chords/2/")
    client.get("/api/v1/data/chords/999/")

    response = client.get("/metrics/")
    content = response.content.decode("utf-8")

    assert "{id}" in content
    assert 'endpoint="/api/v1/data/chords/1/"' not in content
    assert 'endpoint="/api/v1/data/chords/2/"' not in content


@pytest.mark.integration
@pytest.mark.django_db
def test_app_info_metric_set_on_startup(client: Client) -> None:
    """Test that app_info metric is set when the app starts."""
    response = client.get("/metrics/")
    content = response.content.decode("utf-8")

    assert "guitar0_backend_app_info" in content
    assert "version=" in content
    assert "git_sha=" in content
    assert "build_datetime=" in content
