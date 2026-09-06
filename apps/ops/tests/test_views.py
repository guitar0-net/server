# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for the ops views."""

import pytest
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from prometheus_client import CONTENT_TYPE_LATEST

from apps.ops import views


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


def test_metrics_stays_reachable_at_its_original_url() -> None:
    assert reverse("ops:prometheus") == "/metrics/"


@pytest.mark.django_db
def test_health_view_answers_that_the_process_is_alive(client: Client) -> None:
    assert client.get("/health/").json() == {"status": "ok"}


@pytest.mark.django_db
def test_health_view_succeeds(client: Client) -> None:
    assert client.get("/health/").status_code == 200


@pytest.mark.django_db
def test_health_view_forbids_caching_its_answer(client: Client) -> None:
    assert client.get("/health/")["Cache-Control"] == "no-store"


@pytest.mark.django_db
def test_health_view_queries_no_database(client: Client) -> None:
    # A database blip must not make the container healthcheck restart a
    # process that still serves traffic.
    with CaptureQueriesContext(connection) as queries:
        client.get("/health/")

    assert len(queries) == 0


@pytest.mark.django_db
def test_health_view_rejects_a_post(client: Client) -> None:
    assert client.post("/health/").status_code == 405


@pytest.mark.django_db
def test_ready_view_succeeds_while_the_database_answers(client: Client) -> None:
    assert client.get("/ready/").status_code == 200


@pytest.mark.django_db
def test_ready_view_reports_the_database_it_reached(client: Client) -> None:
    assert client.get("/ready/").json() == {"status": "ready", "database": True}


@pytest.mark.django_db
def test_ready_view_fails_while_the_database_is_unreachable(
    client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(views, "is_database_reachable", lambda: False)

    assert client.get("/ready/").status_code == 503


@pytest.mark.django_db
def test_ready_view_reports_the_database_it_cannot_reach(
    client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(views, "is_database_reachable", lambda: False)

    assert client.get("/ready/").json() == {"status": "not ready", "database": False}


@pytest.mark.django_db
def test_ready_view_rejects_a_post(client: Client) -> None:
    assert client.post("/ready/").status_code == 405
