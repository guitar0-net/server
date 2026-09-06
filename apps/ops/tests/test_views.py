# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for the metrics views."""

import pytest
from django.test import Client
from prometheus_client import CONTENT_TYPE_LATEST


@pytest.mark.django_db
def test_metrics_view_returns_200_and_content_type(client: Client) -> None:
    response = client.get("/metrics/")
    assert response.status_code == 200
    assert response["Content-Type"] == CONTENT_TYPE_LATEST


@pytest.mark.django_db
def test_metrics_view_contains_http_metrics_definitions(client: Client) -> None:
    client.get("/api/v1/chords/")

    response = client.get("/metrics/")
    content = response.content.decode("utf-8")

    assert "guitar0_backend_app_info" in content

    assert "guitar0_backend_http_requests_total" in content
    assert "guitar0_backend_http_request_duration_seconds" in content
