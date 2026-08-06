# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Selectors for the donations app."""

from django.db.models import QuerySet

from apps.donations.models import DonationProduct, Purchase


def get_active_donation_products() -> QuerySet[DonationProduct]:
    """Get all donation products currently offered to clients.

    Returns:
        QuerySet[DonationProduct]: Active donation products.
    """
    return DonationProduct.objects.filter(is_active=True)


def get_donation_product(product_id: str) -> DonationProduct | None:
    """Get a donation product by its store product_id, active or not.

    Deliberately not filtered by `is_active`: verifying or reconciling a
    purchase must keep working for a product staff have since retired, or a
    real payment already made against it can get silently auto-refunded by
    the store while we wait on a retry that never comes. Callers that need
    "is this still sellable" (e.g. `verify_and_record_purchase` when no prior
    purchase exists) check `product.is_active` themselves; see
    `get_active_donation_products` for "what can new buyers see".

    Args:
        product_id: The store SKU string, identical on Android and iOS.

    Returns:
        DonationProduct | None: The matching product, or None if it does not
            exist.
    """
    return DonationProduct.objects.filter(product_id=product_id).first()


def get_purchase(platform: str, store_transaction_id: str) -> Purchase | None:
    """Get a previously recorded purchase by platform and store transaction id.

    Args:
        platform: One of the `Platform` choices.
        store_transaction_id: The store's own transaction identifier.

    Returns:
        Purchase | None: The matching purchase, or None if never recorded.
    """
    return (
        Purchase.objects
        .filter(platform=platform, store_transaction_id=store_transaction_id)
        .select_related("product", "user")
        .first()
    )


def get_unclaimed_purchases_for_device(device_id: str) -> QuerySet[Purchase]:
    """Get anonymous purchases recorded for a device that no user owns yet.

    Args:
        device_id: The client-generated device UUID.

    Returns:
        QuerySet[Purchase]: Purchases tagged with this device_id and no user.
    """
    return Purchase.objects.filter(device_id=device_id, user__isnull=True)
