# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Thin client for the Google Play Developer API (one-time products).

Isolated from services.py so the HTTP/auth details of talking to Google stay
out of the business logic, and so tests can stub `_build_authorized_session`
instead of mocking `requests` calls scattered across the module.
"""

import json
from typing import Any
from urllib.parse import quote

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account

_SCOPES = ["https://www.googleapis.com/auth/androidpublisher"]
_BASE_URL = "https://androidpublisher.googleapis.com/androidpublisher/v3/applications"
_TIMEOUT_SECONDS = 10


class GooglePlayError(Exception):
    """Base class for Google Play Developer API failures."""


class PurchaseNotFoundError(GooglePlayError):
    """No purchase exists for this product_id/purchase_token pair."""


class PurchaseAlreadyAcknowledgedError(GooglePlayError):
    """The purchase was already acknowledged by a previous call."""


class GooglePlayCommunicationError(GooglePlayError):
    """The Play Developer API could not be reached, or returned an error."""


def _build_authorized_session() -> AuthorizedSession:
    """Build an OAuth2-authorized session for the Play Developer API.

    Isolated in its own function so tests can stub out the network entirely.

    Returns:
        AuthorizedSession: A `requests.Session` that attaches a valid bearer
            token to every request, refreshing it as needed.

    Raises:
        ImproperlyConfigured: If GOOGLE_PLAY_SERVICE_ACCOUNT_INFO is not set.
    """
    if not settings.GOOGLE_PLAY_SERVICE_ACCOUNT_INFO:
        raise ImproperlyConfigured(
            "GOOGLE_PLAY_SERVICE_ACCOUNT_INFO must be configured to call the "
            "Play Developer API."
        )
    info = json.loads(settings.GOOGLE_PLAY_SERVICE_ACCOUNT_INFO)
    credentials = service_account.Credentials.from_service_account_info(  # type: ignore[no-untyped-call]
        info, scopes=_SCOPES
    )
    return AuthorizedSession(credentials)  # type: ignore[no-untyped-call]


def _purchase_token_url(
    product_id: str, purchase_token: str, *, suffix: str = ""
) -> str:
    """Build the Play Developer API URL for a specific purchase token.

    Shared by `get_purchase` and `acknowledge_purchase` so the package name
    check and path structure live in one place.

    Raises:
        ImproperlyConfigured: If GOOGLE_PLAY_PACKAGE_NAME is not set.
    """
    if not settings.GOOGLE_PLAY_PACKAGE_NAME:
        raise ImproperlyConfigured(
            "GOOGLE_PLAY_PACKAGE_NAME must be configured to call the Play "
            "Developer API."
        )
    return (
        f"{_BASE_URL}/{quote(settings.GOOGLE_PLAY_PACKAGE_NAME, safe='')}"
        f"/purchases/products/{quote(product_id, safe='')}"
        f"/tokens/{quote(purchase_token, safe='')}{suffix}"
    )


def get_purchase(*, product_id: str, purchase_token: str) -> dict[str, Any]:
    """Fetch a one-time product purchase's current state from Google Play.

    Args:
        product_id: The store SKU the purchase was made for.
        purchase_token: The opaque token the client received from Play Billing.

    Returns:
        dict[str, Any]: The purchase resource, as returned by Google.

    Raises:
        PurchaseNotFoundError: If Google has no record of this token/product.
        GooglePlayCommunicationError: On any other non-2xx response, or if
            the request could not be sent at all.
    """
    url = _purchase_token_url(product_id, purchase_token)
    try:
        response = _build_authorized_session().get(url, timeout=_TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        raise GooglePlayCommunicationError(str(exc)) from exc

    if response.status_code == requests.codes.not_found:
        raise PurchaseNotFoundError(f"No purchase found for token {purchase_token!r}")
    if not response.ok:
        raise GooglePlayCommunicationError(
            f"Google Play returned {response.status_code}: {response.text}"
        )
    return response.json()  # type: ignore[no-any-return]


def acknowledge_purchase(*, product_id: str, purchase_token: str) -> None:
    """Acknowledge a one-time product purchase, or confirm it's already done.

    Google auto-refunds a purchase left unacknowledged for three days, so
    this must succeed (or already have succeeded) for every real purchase.

    Args:
        product_id: The store SKU the purchase was made for.
        purchase_token: The opaque token the client received from Play Billing.

    Raises:
        PurchaseAlreadyAcknowledgedError: If Google reports the purchase was
            already acknowledged — safe for the caller to treat as success.
        GooglePlayCommunicationError: On any other non-2xx response, or if
            the request could not be sent at all.
    """
    url = _purchase_token_url(product_id, purchase_token, suffix=":acknowledge")
    try:
        response = _build_authorized_session().post(url, timeout=_TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        raise GooglePlayCommunicationError(str(exc)) from exc

    if response.ok:
        return
    if response.status_code == requests.codes.bad_request and _is_already_acknowledged(
        response
    ):
        raise PurchaseAlreadyAcknowledgedError(purchase_token)
    raise GooglePlayCommunicationError(
        f"Google Play returned {response.status_code}: {response.text}"
    )


def _is_already_acknowledged(response: requests.Response) -> bool:
    """Check whether a 400 response is Google's "already acknowledged" error."""
    try:
        body = response.json()
    except ValueError:
        return False
    message = str(body.get("error", {}).get("message", ""))
    return "acknowledg" in message.lower()
