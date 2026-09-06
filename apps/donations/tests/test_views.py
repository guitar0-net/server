# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for donations API views."""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models.user import User
from apps.accounts.tests.factories.user import UserFactory
from apps.donations.constants import Platform
from apps.donations.models import Purchase
from apps.donations.services import (
    PurchasePendingError,
    PurchaseVerificationError,
    StoreCommunicationError,
    UnknownDonationProductError,
)
from apps.donations.tests.factories import DonationProductFactory, PurchaseFactory


@pytest.mark.django_db
def test_donation_products_list_excludes_inactive_products(
    api_client: APIClient,
) -> None:
    DonationProductFactory.create(product_id="active-tier", is_active=True)
    DonationProductFactory.create(product_id="retired-tier", is_active=False)

    response = api_client.get(reverse("donation-products"))

    assert [p["product_id"] for p in response.data["results"]] == ["active-tier"]


@pytest.mark.django_db
def test_purchase_verify_returns_the_completed_purchase(
    api_client: APIClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    product = DonationProductFactory.create(product_id="thank-you")
    completed = PurchaseFactory.create(product=product)
    monkeypatch.setattr(
        "apps.donations.api.v1.views.verify_and_record_purchase",
        lambda **_kwargs: completed,
    )

    response = api_client.post(
        reverse("donation-verify"),
        {
            "platform": Platform.ANDROID,
            "product_id": "thank-you",
            "store_transaction_id": "tx-1",
            "purchase_token": "token-1",
        },
        format="json",
    )

    assert response.data["status"] == completed.status


@pytest.mark.django_db
def test_purchase_verify_passes_the_authenticated_user_to_the_service(
    api_client: APIClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    product = DonationProductFactory.create(product_id="thank-you")
    caller = UserFactory.create(email="автор-доната@example.com")
    completed = PurchaseFactory.create(product=product, user=caller)
    captured_users: list[User | None] = []

    def _stub(  # noqa: PLR0913
        *,
        platform: str,
        product_id: str,
        store_transaction_id: str,
        purchase_token: str,
        signed_transaction_info: str,
        user: User | None,
        device_id: str,
    ) -> Purchase:
        captured_users.append(user)
        return completed

    monkeypatch.setattr("apps.donations.api.v1.views.verify_and_record_purchase", _stub)
    access = str(RefreshToken.for_user(caller).access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    api_client.post(
        reverse("donation-verify"),
        {
            "platform": Platform.ANDROID,
            "product_id": "thank-you",
            "store_transaction_id": "tx-auth",
            "purchase_token": "token-auth",
        },
        format="json",
    )

    assert captured_users == [caller]


@pytest.mark.django_db
def test_purchase_verify_returns_400_for_a_missing_android_purchase_token(
    api_client: APIClient,
) -> None:
    response = api_client.post(
        reverse("donation-verify"),
        {
            "platform": Platform.ANDROID,
            "product_id": "thank-you",
            "store_transaction_id": "tx-2",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_purchase_verify_returns_400_for_a_missing_ios_signed_transaction(
    api_client: APIClient,
) -> None:
    response = api_client.post(
        reverse("donation-verify"),
        {
            "platform": Platform.IOS,
            "product_id": "thank-you",
            "store_transaction_id": "tx-ios",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_purchase_verify_returns_400_for_an_unknown_product(
    api_client: APIClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _raise(**_kwargs: object) -> None:
        raise UnknownDonationProductError("ghost-product")

    monkeypatch.setattr(
        "apps.donations.api.v1.views.verify_and_record_purchase", _raise
    )

    response = api_client.post(
        reverse("donation-verify"),
        {
            "platform": Platform.IOS,
            "product_id": "ghost-product",
            "store_transaction_id": "tx-3",
            "signed_transaction_info": "jws-3",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_purchase_verify_returns_422_for_a_rejected_purchase(
    api_client: APIClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _raise(**_kwargs: object) -> None:
        raise PurchaseVerificationError("not in purchased state")

    monkeypatch.setattr(
        "apps.donations.api.v1.views.verify_and_record_purchase", _raise
    )

    response = api_client.post(
        reverse("donation-verify"),
        {
            "platform": Platform.IOS,
            "product_id": "thank-you",
            "store_transaction_id": "tx-4",
            "signed_transaction_info": "jws-4",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.django_db
def test_purchase_verify_returns_409_for_a_purchase_pending_payment(
    api_client: APIClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _raise(**_kwargs: object) -> None:
        raise PurchasePendingError("платёж ещё не прошёл")

    monkeypatch.setattr(
        "apps.donations.api.v1.views.verify_and_record_purchase", _raise
    )

    response = api_client.post(
        reverse("donation-verify"),
        {
            "platform": Platform.ANDROID,
            "product_id": "спасибо",
            "store_transaction_id": "GPA.tx-ожидание",
            "purchase_token": "токен-ожидание",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.django_db
def test_purchase_verify_accepts_an_android_request_without_a_transaction_id(
    api_client: APIClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _raise(**_kwargs: object) -> None:
        raise PurchasePendingError("платёж ещё не прошёл")

    monkeypatch.setattr(
        "apps.donations.api.v1.views.verify_and_record_purchase", _raise
    )

    response = api_client.post(
        reverse("donation-verify"),
        {
            "platform": Platform.ANDROID,
            "product_id": "спасибо-без-заказа",
            "purchase_token": "токен-без-заказа",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.django_db
def test_purchase_verify_rejects_an_ios_request_without_a_transaction_id(
    api_client: APIClient,
) -> None:
    response = api_client.post(
        reverse("donation-verify"),
        {
            "platform": Platform.IOS,
            "product_id": "спасибо-ios",
            "signed_transaction_info": "jws-без-идентификатора",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_purchase_verify_returns_502_when_the_store_is_unreachable(
    api_client: APIClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _raise(**_kwargs: object) -> None:
        raise StoreCommunicationError("timed out")

    monkeypatch.setattr(
        "apps.donations.api.v1.views.verify_and_record_purchase", _raise
    )

    response = api_client.post(
        reverse("donation-verify"),
        {
            "platform": Platform.IOS,
            "product_id": "thank-you",
            "store_transaction_id": "tx-5",
            "signed_transaction_info": "jws-5",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_502_BAD_GATEWAY


@pytest.mark.django_db
def test_purchase_verify_returns_429_after_five_requests_in_a_minute(
    api_client: APIClient,
) -> None:
    for _ in range(5):
        api_client.post(reverse("donation-verify"), {}, format="json")

    response = api_client.post(reverse("donation-verify"), {}, format="json")

    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


@pytest.mark.django_db
def test_claim_device_donations_returns_401_for_an_unauthenticated_request(
    api_client: APIClient,
) -> None:
    response = api_client.post(
        reverse("donation-claim"), {"device_id": "device-1"}, format="json"
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_claim_device_donations_attaches_anonymous_purchases_to_the_caller(
    api_client: APIClient,
) -> None:
    user = UserFactory.create()
    anonymous = PurchaseFactory.create(device_id="устройство-1", user=None)
    access = str(RefreshToken.for_user(user).access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    api_client.post(
        reverse("donation-claim"), {"device_id": "устройство-1"}, format="json"
    )

    anonymous.refresh_from_db()
    assert anonymous.user_id == user.pk
