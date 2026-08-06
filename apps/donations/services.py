# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Services for the donations app: purchase verification and claiming."""

from decimal import Decimal

import attrs
from appstoreserverlibrary.models.JWSTransactionDecodedPayload import (
    JWSTransactionDecodedPayload,
)
from django.db import IntegrityError

from apps.accounts.models.user import User
from apps.donations import app_store_client, google_play_client
from apps.donations.constants import Platform, PurchaseStatus
from apps.donations.models import DonationProduct, Purchase
from apps.donations.selectors import (
    get_donation_product,
    get_purchase,
    get_unclaimed_purchases_for_device,
)


class UnknownDonationProductError(Exception):
    """Raised when product_id can't be sold as a new purchase right now.

    Covers both a product_id that matches no DonationProduct at all, and one
    that matches a product staff have deactivated *and* has no purchase
    already recorded against it — a deactivated product with an existing
    purchase is still verified/reconciled normally, see
    `verify_and_record_purchase`.
    """


class PurchaseVerificationError(Exception):
    """Raised when the store confirms the purchase does not check out.

    Covers a token/transaction that does not exist, belongs to a different
    product, is not in a purchased state, was revoked, or whose claimed
    store_transaction_id doesn't match what the store reports. The caller
    sent bad data — retrying the same request will not help.
    """


class StoreCommunicationError(Exception):
    """Raised when Google Play is unreachable.

    A transient failure (network error, timeout, 5xx) — the caller should be
    told to retry rather than treated as an invalid purchase.
    """


def verify_and_record_purchase(  # noqa: PLR0913
    *,
    platform: str,
    product_id: str,
    store_transaction_id: str,
    purchase_token: str,
    signed_transaction_info: str,
    user: User | None,
    device_id: str,
) -> Purchase:
    """Verify a store purchase and record it, claiming it for `user` if known.

    Both platforms follow the same shape: verify a store-issued artifact the
    client can't have forged (Android's `purchase_token`, iOS's signed
    transaction JWS), then use the store's own transaction id from that
    verified response — never the client-submitted `store_transaction_id`
    directly — as the idempotency key. A submitted id that disagrees with the
    store's is rejected outright rather than silently overwritten or ignored.

    If the existing row has no user yet and this call is authenticated, it is
    attached to `user` here — this is the restore-purchases path after a
    reinstall or new device, not just a retry on the same device.

    Args:
        platform: One of the `Platform` choices.
        product_id: The store SKU the client believes it purchased.
        store_transaction_id: The store's own transaction identifier, as
            claimed by the client; cross-checked against the verified
            response for both platforms.
        purchase_token: Android's opaque purchase token. Unused for iOS.
        signed_transaction_info: iOS's signed transaction JWS from StoreKit.
            Unused for Android.
        user: The authenticated user making the request, or None if anonymous.
        device_id: Client-generated device UUID, used when `user` is None.

    Returns:
        Purchase: The verified, persisted purchase record.

    Raises:
        UnknownDonationProductError: If product_id is unknown, or names a
            deactivated product with no purchase already recorded for it.
        PurchaseVerificationError: If the store rejects the purchase, or the
            store's own transaction id doesn't match the id claimed by the
            client.
        StoreCommunicationError: If Google Play cannot be reached.
    """
    product = get_donation_product(product_id)
    if product is None:
        raise UnknownDonationProductError(product_id)

    if platform == Platform.ANDROID:
        return _verify_android_purchase(
            product=product,
            claimed_store_transaction_id=store_transaction_id,
            purchase_token=purchase_token,
            user=user,
            device_id=device_id,
        )
    if platform == Platform.IOS:
        return _verify_ios_purchase(
            product=product,
            claimed_store_transaction_id=store_transaction_id,
            signed_transaction_info=signed_transaction_info,
            user=user,
            device_id=device_id,
        )
    # Unreachable through the API: PurchaseVerifyRequestSerializer restricts
    # platform to Platform.choices. Kept as a safety net for direct callers.
    raise UnknownDonationProductError(product_id)


def claim_device_purchases(user: User, device_id: str) -> int:
    """Attach every unclaimed purchase for a device to a user.

    Meant to be called once after login, so a donation made anonymously on
    the same device before signing in doesn't require a store-side restore.

    Args:
        user: The now-authenticated user.
        device_id: The client-generated device UUID to look up.

    Returns:
        int: Number of purchases attached to the user.
    """
    purchases = list(get_unclaimed_purchases_for_device(device_id))
    for purchase in purchases:
        _reconcile_existing_purchase(purchase, user=user)
    return len(purchases)


def _reconcile_existing_purchase(purchase: Purchase, *, user: User | None) -> Purchase:
    """Bring an already-recorded purchase in line with the current request.

    Attaches `user` if the purchase is still anonymous, and retries the
    Android acknowledge if a previous attempt recorded the purchase but never
    confirmed acknowledgement (network failure between the two calls).
    """
    if purchase.user is None and user is not None:
        purchase.user = user
        purchase.device_id = ""
        purchase.save(update_fields=["user", "device_id"])

    if (
        purchase.platform == Platform.ANDROID
        and purchase.status == PurchaseStatus.VERIFIED
    ):
        _acknowledge_android_purchase(purchase)

    return purchase


def _create_purchase_or_recover_from_race(
    *,
    platform: str,
    store_transaction_id: str,
    user: User | None,
    **create_kwargs: object,
) -> tuple[Purchase, bool]:
    """Create a Purchase row, tolerating a concurrent duplicate submission.

    Two requests for the same (platform, store_transaction_id) — e.g. a
    mobile client retrying a verify call that timed out before the response
    arrived — can both pass the "not recorded yet" check in
    `verify_and_record_purchase` before either has inserted. The loser then
    hits `unique_platform_transaction` instead of getting a clean row back;
    recover by reconciling against whatever the winner wrote instead of
    letting a raw IntegrityError surface as an unhandled 500.

    Returns:
        tuple[Purchase, bool]: The purchase, and whether this call created it
            (False means the row already existed and was reconciled instead —
            callers must not repeat store-side effects like acknowledging).
    """
    try:
        purchase = Purchase.objects.create(
            platform=platform,
            store_transaction_id=store_transaction_id,
            user=user,
            **create_kwargs,
        )
    except IntegrityError:
        existing = get_purchase(platform, store_transaction_id)
        if existing is None:
            raise
        return _reconcile_existing_purchase(existing, user=user), False
    return purchase, True


def _verify_android_purchase(
    *,
    product: DonationProduct,
    claimed_store_transaction_id: str,
    purchase_token: str,
    user: User | None,
    device_id: str,
) -> Purchase:
    """Verify an Android purchase and reconcile or create its Purchase row.

    The row is keyed on Google's own `orderId`, fetched from the purchase
    resource itself — `purchase_token` has no client-verifiable id of its
    own, so `claimed_store_transaction_id` is only ever used to cross-check
    against it, never written to the database directly.
    """
    try:
        response = google_play_client.get_purchase(
            product_id=product.product_id, purchase_token=purchase_token
        )
    except google_play_client.PurchaseNotFoundError as exc:
        raise PurchaseVerificationError(str(exc)) from exc
    except google_play_client.GooglePlayCommunicationError as exc:
        raise StoreCommunicationError(str(exc)) from exc

    if response.get("purchaseState") != 0:
        raise PurchaseVerificationError(
            f"Purchase is not in the purchased state: {response.get('purchaseState')!r}"
        )

    order_id = response.get("orderId")
    if not isinstance(order_id, str) or not order_id:
        raise PurchaseVerificationError("Google Play response is missing an orderId.")
    if order_id != claimed_store_transaction_id:
        raise PurchaseVerificationError(
            "store_transaction_id does not match Google's orderId for this purchase."
        )

    existing = get_purchase(Platform.ANDROID, order_id)
    if existing is not None:
        return _reconcile_existing_purchase(existing, user=user)

    if not product.is_active:
        raise UnknownDonationProductError(product.product_id)

    # amount/currency stay unset here: Google's purchases.products resource
    # doesn't report price, unlike Apple's transaction payload.
    purchase, created = _create_purchase_or_recover_from_race(
        platform=Platform.ANDROID,
        store_transaction_id=order_id,
        user=user,
        product=product,
        purchase_token=purchase_token,
        device_id="" if user is not None else device_id,
        status=PurchaseStatus.VERIFIED,
        raw_response=response,
    )
    if created:
        _acknowledge_android_purchase(purchase)
    return purchase


def _acknowledge_android_purchase(purchase: Purchase) -> None:
    """Acknowledge an Android purchase, tolerating a prior successful attempt.

    Google auto-refunds an unacknowledged purchase after three days, so this
    must run every time we see a VERIFIED-but-not-COMPLETED row — including
    on retry, if the previous attempt verified the purchase but then failed
    to reach the acknowledge endpoint.
    """
    try:
        google_play_client.acknowledge_purchase(
            product_id=purchase.product.product_id,
            purchase_token=purchase.purchase_token,
        )
    except google_play_client.PurchaseAlreadyAcknowledgedError:
        # A previous attempt already acknowledged it with Google — fine, we
        # still need to mark the purchase COMPLETED below.
        pass
    except google_play_client.GooglePlayCommunicationError as exc:
        raise StoreCommunicationError(str(exc)) from exc

    purchase.status = PurchaseStatus.COMPLETED
    purchase.save(update_fields=["status"])


def _verify_ios_purchase(
    *,
    product: DonationProduct,
    claimed_store_transaction_id: str,
    signed_transaction_info: str,
    user: User | None,
    device_id: str,
) -> Purchase:
    """Verify an iOS purchase and reconcile or create its Purchase row.

    The row is keyed on Apple's own `transactionId`, read from the verified
    JWS payload — `claimed_store_transaction_id` is only ever used to
    cross-check against it, never written to the database directly.
    """
    try:
        response = app_store_client.verify_signed_transaction(signed_transaction_info)
    except app_store_client.TransactionVerificationError as exc:
        raise PurchaseVerificationError(str(exc)) from exc

    if response.productId != product.product_id:
        raise PurchaseVerificationError(
            f"Transaction is for a different product: {response.productId!r}"
        )
    if response.revocationDate is not None:
        raise PurchaseVerificationError("Transaction was revoked by Apple.")

    transaction_id = response.transactionId
    if not transaction_id:
        raise PurchaseVerificationError("Apple's response is missing a transactionId.")
    if transaction_id != claimed_store_transaction_id:
        raise PurchaseVerificationError(
            "store_transaction_id does not match Apple's transactionId "
            "for this transaction."
        )

    existing = get_purchase(Platform.IOS, transaction_id)
    if existing is not None:
        return _reconcile_existing_purchase(existing, user=user)

    if not product.is_active:
        raise UnknownDonationProductError(product.product_id)

    amount, currency = _extract_apple_price(response)
    purchase, _ = _create_purchase_or_recover_from_race(
        platform=Platform.IOS,
        store_transaction_id=transaction_id,
        user=user,
        product=product,
        device_id="" if user is not None else device_id,
        status=PurchaseStatus.COMPLETED,
        amount=amount,
        currency=currency,
        environment=response.environment.value if response.environment else "",
        raw_response=attrs.asdict(response),
    )
    return purchase


def _extract_apple_price(
    response: JWSTransactionDecodedPayload,
) -> tuple[Decimal | None, str]:
    """Read the price Apple charged, when the transaction payload includes it.

    Apple reports `price` in milliunits of `currency` (e.g. 990 = 0.99). Not
    every transaction includes these fields, so both are best-effort and
    only ever used for reporting, never for granting or denying a purchase.
    """
    if response.price is None or not response.currency:
        return None, ""
    return Decimal(response.price) / Decimal(1000), response.currency
