# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for donations services."""

from decimal import Decimal
from typing import Any

import pytest
from appstoreserverlibrary.models.Environment import Environment
from appstoreserverlibrary.models.JWSTransactionDecodedPayload import (
    JWSTransactionDecodedPayload,
)
from django.db import IntegrityError

from apps.accounts.tests.factories.user import UserFactory
from apps.donations import app_store_client, google_play_client
from apps.donations.constants import Platform, PurchaseStatus
from apps.donations.models import Purchase
from apps.donations.services import (
    PurchaseVerificationError,
    StoreCommunicationError,
    UnknownDonationProductError,
    claim_device_purchases,
    verify_and_record_purchase,
)
from apps.donations.tests.factories import DonationProductFactory, PurchaseFactory


def _stub_google_get_purchase(
    monkeypatch: pytest.MonkeyPatch, response: dict[str, Any]
) -> None:
    monkeypatch.setattr(
        "apps.donations.services.google_play_client.get_purchase",
        lambda **_kwargs: response,
    )


def _stub_google_acknowledge(
    monkeypatch: pytest.MonkeyPatch, *, error: Exception | None = None
) -> None:
    def _stub(**_kwargs: object) -> None:
        if error is not None:
            raise error

    monkeypatch.setattr(
        "apps.donations.services.google_play_client.acknowledge_purchase", _stub
    )


def _stub_apple_verify_signed_transaction(  # noqa: PLR0913
    monkeypatch: pytest.MonkeyPatch,
    *,
    transaction_id: str,
    product_id: str,
    price: int | None = None,
    currency: str | None = None,
    revocation_date: int | None = None,
    environment: Environment | None = None,
) -> None:
    transaction = JWSTransactionDecodedPayload(
        transactionId=transaction_id,
        productId=product_id,
        price=price,
        currency=currency,
        revocationDate=revocation_date,
        environment=environment,
    )
    monkeypatch.setattr(
        "apps.donations.services.app_store_client.verify_signed_transaction",
        lambda _signed_transaction_info: transaction,
    )


@pytest.mark.django_db
def test_verify_and_record_purchase_raises_for_unknown_product() -> None:
    with pytest.raises(UnknownDonationProductError):
        verify_and_record_purchase(
            platform=Platform.ANDROID,
            product_id="does-not-exist",
            store_transaction_id="tx-1",
            purchase_token="token-1",
            signed_transaction_info="",
            user=None,
            device_id="device-1",
        )


@pytest.mark.django_db
def test_verify_and_record_purchase_rejects_a_platform_that_is_neither_store() -> None:
    product = DonationProductFactory.create()

    with pytest.raises(UnknownDonationProductError):
        verify_and_record_purchase(
            platform="телевизор",
            product_id=product.product_id,
            store_transaction_id="tx-bogus",
            purchase_token="",
            signed_transaction_info="",
            user=None,
            device_id="device-1",
        )


@pytest.mark.django_db
def test_verify_and_record_purchase_rejects_a_new_android_purchase_for_retired_product(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    product = DonationProductFactory.create(is_active=False)
    _stub_google_get_purchase(
        monkeypatch, {"purchaseState": 0, "orderId": "GPA.tx-retired"}
    )

    with pytest.raises(UnknownDonationProductError):
        verify_and_record_purchase(
            platform=Platform.ANDROID,
            product_id=product.product_id,
            store_transaction_id="GPA.tx-retired",
            purchase_token="token-retired",
            signed_transaction_info="",
            user=None,
            device_id="device-1",
        )


@pytest.mark.django_db
def test_verify_and_record_purchase_retries_acknowledge_for_a_retired_products_purchase(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A resubmission must still recover a stuck purchase after its product is retired.

    Reconciling an already-recorded purchase must not depend on the product
    still being sellable — otherwise deactivating a product traps any
    VERIFIED-but-unacknowledged row for it, and Google auto-refunds it after
    three days with nothing left to retry the acknowledge.
    """
    product = DonationProductFactory.create()
    unacknowledged = PurchaseFactory.create(
        platform=Platform.ANDROID,
        product=product,
        store_transaction_id="GPA.tx-retire-race",
        purchase_token="token-retire-race",
        status=PurchaseStatus.VERIFIED,
        user=None,
        device_id="device-1",
    )
    product.is_active = False
    product.save(update_fields=["is_active"])
    _stub_google_get_purchase(
        monkeypatch, {"purchaseState": 0, "orderId": "GPA.tx-retire-race"}
    )
    _stub_google_acknowledge(monkeypatch)

    verify_and_record_purchase(
        platform=Platform.ANDROID,
        product_id=product.product_id,
        store_transaction_id="GPA.tx-retire-race",
        purchase_token="token-retire-race",
        signed_transaction_info="",
        user=None,
        device_id="device-1",
    )

    unacknowledged.refresh_from_db()
    assert unacknowledged.status == PurchaseStatus.COMPLETED


@pytest.mark.django_db
def test_verify_and_record_purchase_creates_completed_android_purchase(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    product = DonationProductFactory.create(product_id="thank-you")
    _stub_google_get_purchase(monkeypatch, {"purchaseState": 0, "orderId": "GPA.tx-1"})
    _stub_google_acknowledge(monkeypatch)

    purchase = verify_and_record_purchase(
        platform=Platform.ANDROID,
        product_id=product.product_id,
        store_transaction_id="GPA.tx-1",
        purchase_token="token-1",
        signed_transaction_info="",
        user=None,
        device_id="device-1",
    )

    assert purchase.status == PurchaseStatus.COMPLETED


@pytest.mark.django_db
def test_verify_and_record_purchase_tags_anonymous_android_purchase_with_device_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    product = DonationProductFactory.create()
    _stub_google_get_purchase(monkeypatch, {"purchaseState": 0, "orderId": "GPA.tx-2"})
    _stub_google_acknowledge(monkeypatch)

    purchase = verify_and_record_purchase(
        platform=Platform.ANDROID,
        product_id=product.product_id,
        store_transaction_id="GPA.tx-2",
        purchase_token="token-2",
        signed_transaction_info="",
        user=None,
        device_id="устройство-42",
    )

    assert purchase.device_id == "устройство-42"


@pytest.mark.django_db
def test_verify_and_record_purchase_attaches_authenticated_user_directly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    product = DonationProductFactory.create()
    user = UserFactory.create()
    _stub_google_get_purchase(monkeypatch, {"purchaseState": 0, "orderId": "GPA.tx-3"})
    _stub_google_acknowledge(monkeypatch)

    purchase = verify_and_record_purchase(
        platform=Platform.ANDROID,
        product_id=product.product_id,
        store_transaction_id="GPA.tx-3",
        purchase_token="token-3",
        signed_transaction_info="",
        user=user,
        device_id="",
    )

    assert purchase.user_id == user.pk


@pytest.mark.django_db
def test_verify_and_record_purchase_rejects_android_purchase_not_in_purchased_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    product = DonationProductFactory.create()
    _stub_google_get_purchase(monkeypatch, {"purchaseState": 1})

    with pytest.raises(PurchaseVerificationError):
        verify_and_record_purchase(
            platform=Platform.ANDROID,
            product_id=product.product_id,
            store_transaction_id="GPA.tx-4",
            purchase_token="token-4",
            signed_transaction_info="",
            user=None,
            device_id="device-1",
        )


@pytest.mark.django_db
def test_verify_and_record_purchase_rejects_a_claimed_id_google_does_not_confirm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    product = DonationProductFactory.create()
    _stub_google_get_purchase(
        monkeypatch, {"purchaseState": 0, "orderId": "GPA.real-order"}
    )

    with pytest.raises(PurchaseVerificationError):
        verify_and_record_purchase(
            platform=Platform.ANDROID,
            product_id=product.product_id,
            store_transaction_id="GPA.someone-elses-claim",
            purchase_token="token-shared",
            signed_transaction_info="",
            user=None,
            device_id="device-1",
        )

    assert not Purchase.objects.filter(
        store_transaction_id="GPA.someone-elses-claim"
    ).exists()


@pytest.mark.django_db
def test_verify_and_record_purchase_rejects_a_response_missing_an_order_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    product = DonationProductFactory.create()
    _stub_google_get_purchase(monkeypatch, {"purchaseState": 0})

    with pytest.raises(PurchaseVerificationError):
        verify_and_record_purchase(
            platform=Platform.ANDROID,
            product_id=product.product_id,
            store_transaction_id="GPA.tx-no-order-id",
            purchase_token="token-no-order-id",
            signed_transaction_info="",
            user=None,
            device_id="device-1",
        )


@pytest.mark.django_db
def test_verify_and_record_purchase_wraps_a_not_found_android_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    product = DonationProductFactory.create()

    def _raise(**_kwargs: object) -> None:
        raise google_play_client.PurchaseNotFoundError("gone")

    monkeypatch.setattr(
        "apps.donations.services.google_play_client.get_purchase", _raise
    )

    with pytest.raises(PurchaseVerificationError):
        verify_and_record_purchase(
            platform=Platform.ANDROID,
            product_id=product.product_id,
            store_transaction_id="GPA.tx-5",
            purchase_token="bad-token",
            signed_transaction_info="",
            user=None,
            device_id="device-1",
        )


@pytest.mark.django_db
def test_verify_and_record_purchase_wraps_a_google_play_outage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    product = DonationProductFactory.create()

    def _raise(**_kwargs: object) -> None:
        raise google_play_client.GooglePlayCommunicationError("timed out")

    monkeypatch.setattr(
        "apps.donations.services.google_play_client.get_purchase", _raise
    )

    with pytest.raises(StoreCommunicationError):
        verify_and_record_purchase(
            platform=Platform.ANDROID,
            product_id=product.product_id,
            store_transaction_id="GPA.tx-6",
            purchase_token="token-6",
            signed_transaction_info="",
            user=None,
            device_id="device-1",
        )


@pytest.mark.django_db
def test_verify_and_record_purchase_persists_a_verified_row_when_acknowledge_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    product = DonationProductFactory.create()
    _stub_google_get_purchase(monkeypatch, {"purchaseState": 0, "orderId": "GPA.tx-7"})
    _stub_google_acknowledge(
        monkeypatch, error=google_play_client.GooglePlayCommunicationError("timed out")
    )

    with pytest.raises(StoreCommunicationError):
        verify_and_record_purchase(
            platform=Platform.ANDROID,
            product_id=product.product_id,
            store_transaction_id="GPA.tx-7",
            purchase_token="token-7",
            signed_transaction_info="",
            user=None,
            device_id="device-1",
        )

    stored = Purchase.objects.get(store_transaction_id="GPA.tx-7")
    assert stored.status == PurchaseStatus.VERIFIED


@pytest.mark.django_db
def test_verify_and_record_purchase_retries_acknowledge_on_resubmission(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    product = DonationProductFactory.create()
    unacknowledged = PurchaseFactory.create(
        platform=Platform.ANDROID,
        product=product,
        store_transaction_id="GPA.tx-8",
        purchase_token="token-8",
        status=PurchaseStatus.VERIFIED,
        user=None,
        device_id="device-1",
    )
    _stub_google_get_purchase(monkeypatch, {"purchaseState": 0, "orderId": "GPA.tx-8"})
    _stub_google_acknowledge(monkeypatch)

    verify_and_record_purchase(
        platform=Platform.ANDROID,
        product_id=product.product_id,
        store_transaction_id="GPA.tx-8",
        purchase_token="token-8",
        signed_transaction_info="",
        user=None,
        device_id="device-1",
    )

    unacknowledged.refresh_from_db()
    assert unacknowledged.status == PurchaseStatus.COMPLETED


@pytest.mark.django_db
def test_verify_and_record_purchase_treats_already_acknowledged_as_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    product = DonationProductFactory.create()
    _stub_google_get_purchase(monkeypatch, {"purchaseState": 0, "orderId": "GPA.tx-9"})
    _stub_google_acknowledge(
        monkeypatch,
        error=google_play_client.PurchaseAlreadyAcknowledgedError("already done"),
    )

    purchase = verify_and_record_purchase(
        platform=Platform.ANDROID,
        product_id=product.product_id,
        store_transaction_id="GPA.tx-9",
        purchase_token="token-9",
        signed_transaction_info="",
        user=None,
        device_id="device-1",
    )

    assert purchase.status == PurchaseStatus.COMPLETED


@pytest.mark.django_db
def test_verify_and_record_purchase_recovers_from_a_concurrent_duplicate_insert(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A second request for the same order can lose a race on the insert.

    `_verify_android_purchase` finds no existing row and proceeds to create
    one, but by the time the INSERT runs, a concurrent request for the same
    (platform, store_transaction_id) has already committed its own —
    `unique_platform_transaction` then turns the loser's insert into an
    `IntegrityError` instead of a clean row.
    """
    product = DonationProductFactory.create()
    _stub_google_get_purchase(
        monkeypatch, {"purchaseState": 0, "orderId": "GPA.tx-race"}
    )
    _stub_google_acknowledge(monkeypatch)
    original_create = Purchase.objects.create

    def _lose_the_race(**kwargs: object) -> Purchase:
        original_create(**kwargs)
        raise IntegrityError("duplicate key value violates unique constraint")

    monkeypatch.setattr(Purchase.objects, "create", _lose_the_race)

    purchase = verify_and_record_purchase(
        platform=Platform.ANDROID,
        product_id=product.product_id,
        store_transaction_id="GPA.tx-race",
        purchase_token="token-race",
        signed_transaction_info="",
        user=None,
        device_id="device-race",
    )

    assert purchase.store_transaction_id == "GPA.tx-race"


@pytest.mark.django_db
def test_verify_and_record_purchase_reraises_an_integrity_error_no_row_explains(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An IntegrityError with no matching row to recover from is not swallowed.

    Unlike the race case, no concurrent request explains this failure — there
    is nothing to reconcile against, so it must propagate instead of being
    treated as a recovered duplicate.
    """
    product = DonationProductFactory.create()
    _stub_google_get_purchase(
        monkeypatch, {"purchaseState": 0, "orderId": "GPA.tx-broken"}
    )

    def _raise(**_kwargs: object) -> Purchase:
        raise IntegrityError("some unrelated constraint violation")

    monkeypatch.setattr(Purchase.objects, "create", _raise)

    with pytest.raises(IntegrityError):
        verify_and_record_purchase(
            platform=Platform.ANDROID,
            product_id=product.product_id,
            store_transaction_id="GPA.tx-broken",
            purchase_token="token-broken",
            signed_transaction_info="",
            user=None,
            device_id="device-broken",
        )


@pytest.mark.django_db
def test_verify_and_record_purchase_claims_an_unclaimed_row_on_resubmission(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    product = DonationProductFactory.create()
    user = UserFactory.create()
    anonymous = PurchaseFactory.create(
        platform=Platform.IOS,
        product=product,
        store_transaction_id="tx-restore",
        status=PurchaseStatus.COMPLETED,
        user=None,
        device_id="old-device",
    )
    _stub_apple_verify_signed_transaction(
        monkeypatch, transaction_id="tx-restore", product_id=product.product_id
    )

    verify_and_record_purchase(
        platform=Platform.IOS,
        product_id=product.product_id,
        store_transaction_id="tx-restore",
        purchase_token="",
        signed_transaction_info="jws-restore",
        user=user,
        device_id="",
    )

    anonymous.refresh_from_db()
    assert anonymous.user_id == user.pk


@pytest.mark.django_db
def test_verify_and_record_purchase_does_not_reassign_an_already_claimed_row(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    product = DonationProductFactory.create()
    owner = UserFactory.create(email="владелец@example.com")
    other_user = UserFactory.create(email="чужой@example.com")
    claimed = PurchaseFactory.create(
        platform=Platform.IOS,
        product=product,
        store_transaction_id="tx-owned",
        status=PurchaseStatus.COMPLETED,
        user=owner,
    )
    _stub_apple_verify_signed_transaction(
        monkeypatch, transaction_id="tx-owned", product_id=product.product_id
    )

    verify_and_record_purchase(
        platform=Platform.IOS,
        product_id=product.product_id,
        store_transaction_id="tx-owned",
        purchase_token="",
        signed_transaction_info="jws-owned",
        user=other_user,
        device_id="",
    )

    claimed.refresh_from_db()
    assert claimed.user_id == owner.pk


@pytest.mark.django_db
def test_verify_and_record_purchase_creates_completed_ios_purchase(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    product = DonationProductFactory.create()
    _stub_apple_verify_signed_transaction(
        monkeypatch, transaction_id="tx-ios-1", product_id=product.product_id
    )

    purchase = verify_and_record_purchase(
        platform=Platform.IOS,
        product_id=product.product_id,
        store_transaction_id="tx-ios-1",
        purchase_token="",
        signed_transaction_info="jws-ios-1",
        user=None,
        device_id="device-1",
    )

    assert purchase.status == PurchaseStatus.COMPLETED


@pytest.mark.django_db
def test_verify_and_record_purchase_rejects_a_new_ios_purchase_for_a_retired_product(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    product = DonationProductFactory.create(is_active=False)
    _stub_apple_verify_signed_transaction(
        monkeypatch, transaction_id="tx-ios-retired", product_id=product.product_id
    )

    with pytest.raises(UnknownDonationProductError):
        verify_and_record_purchase(
            platform=Platform.IOS,
            product_id=product.product_id,
            store_transaction_id="tx-ios-retired",
            purchase_token="",
            signed_transaction_info="jws-ios-retired",
            user=None,
            device_id="device-1",
        )


@pytest.mark.django_db
def test_verify_and_record_purchase_records_apples_sandbox_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    product = DonationProductFactory.create()
    _stub_apple_verify_signed_transaction(
        monkeypatch,
        transaction_id="tx-ios-sandbox",
        product_id=product.product_id,
        environment=Environment.SANDBOX,
    )

    purchase = verify_and_record_purchase(
        platform=Platform.IOS,
        product_id=product.product_id,
        store_transaction_id="tx-ios-sandbox",
        purchase_token="",
        signed_transaction_info="jws-ios-sandbox",
        user=None,
        device_id="device-1",
    )

    assert purchase.environment == "Sandbox"


@pytest.mark.django_db
def test_verify_and_record_purchase_extracts_apple_reported_price(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    product = DonationProductFactory.create()
    _stub_apple_verify_signed_transaction(
        monkeypatch,
        transaction_id="tx-ios-2",
        product_id=product.product_id,
        price=990,
        currency="USD",
    )

    purchase = verify_and_record_purchase(
        platform=Platform.IOS,
        product_id=product.product_id,
        store_transaction_id="tx-ios-2",
        purchase_token="",
        signed_transaction_info="jws-ios-2",
        user=None,
        device_id="device-1",
    )

    assert purchase.amount == Decimal("0.99")


@pytest.mark.django_db
def test_verify_and_record_purchase_rejects_ios_transaction_for_a_different_product(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    product = DonationProductFactory.create(product_id="thank-you-small")
    _stub_apple_verify_signed_transaction(
        monkeypatch, transaction_id="tx-ios-3", product_id="thank-you-large"
    )

    with pytest.raises(PurchaseVerificationError):
        verify_and_record_purchase(
            platform=Platform.IOS,
            product_id=product.product_id,
            store_transaction_id="tx-ios-3",
            purchase_token="",
            signed_transaction_info="jws-ios-3",
            user=None,
            device_id="device-1",
        )


@pytest.mark.django_db
def test_verify_and_record_purchase_rejects_a_revoked_ios_transaction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    product = DonationProductFactory.create()
    _stub_apple_verify_signed_transaction(
        monkeypatch,
        transaction_id="tx-ios-4",
        product_id=product.product_id,
        revocation_date=1_700_000_000_000,
    )

    with pytest.raises(PurchaseVerificationError):
        verify_and_record_purchase(
            platform=Platform.IOS,
            product_id=product.product_id,
            store_transaction_id="tx-ios-4",
            purchase_token="",
            signed_transaction_info="jws-ios-4",
            user=None,
            device_id="device-1",
        )


@pytest.mark.django_db
def test_verify_and_record_purchase_rejects_a_claimed_id_apple_does_not_confirm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    product = DonationProductFactory.create()
    _stub_apple_verify_signed_transaction(
        monkeypatch, transaction_id="tx-real", product_id=product.product_id
    )

    with pytest.raises(PurchaseVerificationError):
        verify_and_record_purchase(
            platform=Platform.IOS,
            product_id=product.product_id,
            store_transaction_id="tx-someone-elses-claim",
            purchase_token="",
            signed_transaction_info="jws-mismatched",
            user=None,
            device_id="device-1",
        )

    assert not Purchase.objects.filter(store_transaction_id="tx-real").exists()


@pytest.mark.django_db
def test_verify_and_record_purchase_rejects_a_response_missing_a_transaction_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    product = DonationProductFactory.create()
    _stub_apple_verify_signed_transaction(
        monkeypatch, transaction_id="", product_id=product.product_id
    )

    with pytest.raises(PurchaseVerificationError):
        verify_and_record_purchase(
            platform=Platform.IOS,
            product_id=product.product_id,
            store_transaction_id="tx-ios-no-id",
            purchase_token="",
            signed_transaction_info="jws-no-id",
            user=None,
            device_id="device-1",
        )


@pytest.mark.django_db
def test_verify_and_record_purchase_wraps_an_unverifiable_ios_transaction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    product = DonationProductFactory.create()

    def _raise(_signed_transaction_info: str) -> None:
        raise app_store_client.TransactionVerificationError("bad signature")

    monkeypatch.setattr(
        "apps.donations.services.app_store_client.verify_signed_transaction", _raise
    )

    with pytest.raises(PurchaseVerificationError):
        verify_and_record_purchase(
            platform=Platform.IOS,
            product_id=product.product_id,
            store_transaction_id="tx-ios-7",
            purchase_token="",
            signed_transaction_info="jws-bad-signature",
            user=None,
            device_id="device-1",
        )


@pytest.mark.django_db
def test_claim_device_purchases_returns_the_number_of_rows_claimed() -> None:
    user = UserFactory.create()
    PurchaseFactory.create(device_id="shared-phone", user=None)

    claimed_count = claim_device_purchases(user, "shared-phone")

    assert claimed_count == 1


@pytest.mark.django_db
def test_claim_device_purchases_does_not_touch_a_row_owned_by_someone_else() -> None:
    user = UserFactory.create(email="клеймер@example.com")
    other_owner = UserFactory.create(email="владелец2@example.com")
    already_claimed = PurchaseFactory.create(device_id="shared-phone", user=other_owner)

    claim_device_purchases(user, "shared-phone")

    already_claimed.refresh_from_db()
    assert already_claimed.user_id == other_owner.pk


@pytest.mark.django_db
def test_claim_device_purchases_retries_acknowledge_for_an_unverified_android_row(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Claiming must not leave an unacknowledged Android row behind.

    A row can still be `VERIFIED` (not `COMPLETED`) if a previous verify call
    recorded the purchase but failed to reach Google's acknowledge endpoint.
    Claiming it must retry that acknowledge, the same way resubmitting the
    original verify call would — otherwise Google auto-refunds the purchase
    after three days despite the app now showing it as claimed.
    """
    user = UserFactory.create()
    unacknowledged = PurchaseFactory.create(
        platform=Platform.ANDROID,
        status=PurchaseStatus.VERIFIED,
        user=None,
        device_id="shared-phone",
    )
    _stub_google_acknowledge(monkeypatch)

    claim_device_purchases(user, "shared-phone")

    unacknowledged.refresh_from_db()
    assert unacknowledged.status == PurchaseStatus.COMPLETED
