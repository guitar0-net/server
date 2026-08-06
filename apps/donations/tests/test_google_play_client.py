# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for the Google Play Developer API client."""

from typing import Any

import pytest
import requests
from django.core.exceptions import ImproperlyConfigured

from apps.donations import google_play_client


@pytest.fixture(autouse=True)
def _configure_google_play_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "apps.donations.google_play_client.settings.GOOGLE_PLAY_PACKAGE_NAME",
        "net.guitar0.app",
    )
    monkeypatch.setattr(
        "apps.donations.google_play_client.settings.GOOGLE_PLAY_SERVICE_ACCOUNT_INFO",
        '{"type": "service_account"}',
    )


class _FakeResponse:
    """A stand-in for requests.Response, avoiding a real HTTP mock."""

    def __init__(
        self,
        status_code: int,
        json_body: dict[str, Any] | None = None,
        *,
        unparseable_body: bool = False,
    ) -> None:
        self.status_code = status_code
        self._json_body = json_body or {}
        self._unparseable_body = unparseable_body
        self.ok = 200 <= status_code < 300
        self.text = str(self._json_body)

    def json(self) -> dict[str, Any]:
        if self._unparseable_body:
            raise ValueError("not JSON")
        return self._json_body


class _FakeSession:
    """A stand-in for AuthorizedSession, recording every URL it was asked for."""

    def __init__(self, response: _FakeResponse) -> None:
        self._response = response
        self.requested_urls: list[str] = []

    def get(self, url: str, timeout: int) -> _FakeResponse:
        self.requested_urls.append(url)
        return self._response

    def post(self, url: str, timeout: int) -> _FakeResponse:
        self.requested_urls.append(url)
        return self._response


def _stub_session(
    monkeypatch: pytest.MonkeyPatch, response: _FakeResponse
) -> _FakeSession:
    session = _FakeSession(response)
    monkeypatch.setattr(
        google_play_client, "_build_authorized_session", lambda: session
    )
    return session


def test_get_purchase_returns_the_purchase_resource(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_session(monkeypatch, _FakeResponse(200, {"purchaseState": 0}))

    result = google_play_client.get_purchase(product_id="p1", purchase_token="t1")

    assert result == {"purchaseState": 0}


def test_get_purchase_raises_not_found_for_a_404(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_session(monkeypatch, _FakeResponse(404))

    with pytest.raises(google_play_client.PurchaseNotFoundError):
        google_play_client.get_purchase(product_id="p1", purchase_token="ghost-token")


def test_get_purchase_raises_communication_error_for_a_500(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_session(monkeypatch, _FakeResponse(500))

    with pytest.raises(google_play_client.GooglePlayCommunicationError):
        google_play_client.get_purchase(product_id="p1", purchase_token="t1")


def test_get_purchase_raises_communication_error_when_the_request_itself_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _BrokenSession:
        def get(self, url: str, timeout: int) -> _FakeResponse:
            raise requests.ConnectionError("network down")

    monkeypatch.setattr(google_play_client, "_build_authorized_session", _BrokenSession)

    with pytest.raises(google_play_client.GooglePlayCommunicationError):
        google_play_client.get_purchase(product_id="p1", purchase_token="t1")


def test_acknowledge_purchase_calls_the_acknowledge_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _stub_session(monkeypatch, _FakeResponse(200))

    google_play_client.acknowledge_purchase(product_id="p1", purchase_token="t1")

    assert session.requested_urls[0].endswith("/products/p1/tokens/t1:acknowledge")


def test_acknowledge_purchase_raises_already_acknowledged_for_googles_400(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_session(
        monkeypatch,
        _FakeResponse(
            400,
            {"error": {"message": "The purchase token was already acknowledged."}},
        ),
    )

    with pytest.raises(google_play_client.PurchaseAlreadyAcknowledgedError):
        google_play_client.acknowledge_purchase(product_id="p1", purchase_token="t1")


def test_acknowledge_purchase_raises_communication_error_for_an_unrelated_400(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_session(
        monkeypatch, _FakeResponse(400, {"error": {"message": "Invalid token."}})
    )

    with pytest.raises(google_play_client.GooglePlayCommunicationError):
        google_play_client.acknowledge_purchase(product_id="p1", purchase_token="t1")


def test_acknowledge_purchase_raises_communication_error_for_an_unparseable_400_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_session(monkeypatch, _FakeResponse(400, unparseable_body=True))

    with pytest.raises(google_play_client.GooglePlayCommunicationError):
        google_play_client.acknowledge_purchase(product_id="p1", purchase_token="t1")


def test_acknowledge_purchase_raises_communication_error_when_the_request_itself_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _BrokenSession:
        def post(self, url: str, timeout: int) -> _FakeResponse:
            raise requests.ConnectionError("network down")

    monkeypatch.setattr(google_play_client, "_build_authorized_session", _BrokenSession)

    with pytest.raises(google_play_client.GooglePlayCommunicationError):
        google_play_client.acknowledge_purchase(product_id="p1", purchase_token="t1")


def test_get_purchase_raises_when_the_package_name_is_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "apps.donations.google_play_client.settings.GOOGLE_PLAY_PACKAGE_NAME", None
    )

    with pytest.raises(ImproperlyConfigured):
        google_play_client.get_purchase(product_id="p1", purchase_token="t1")


def test_acknowledge_purchase_raises_when_the_package_name_is_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "apps.donations.google_play_client.settings.GOOGLE_PLAY_PACKAGE_NAME", None
    )

    with pytest.raises(ImproperlyConfigured):
        google_play_client.acknowledge_purchase(product_id="p1", purchase_token="t1")


def test_build_authorized_session_raises_when_service_account_info_is_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "apps.donations.google_play_client.settings.GOOGLE_PLAY_SERVICE_ACCOUNT_INFO",
        None,
    )

    with pytest.raises(ImproperlyConfigured):
        google_play_client._build_authorized_session()
