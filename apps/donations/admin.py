# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Admin settings for the donations app."""

from typing import ClassVar

from django.contrib import admin
from django.http import HttpRequest

from apps.donations.models import DonationProduct, Purchase


@admin.register(DonationProduct)
class DonationProductAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    """Admin interface for the DonationProduct model."""

    list_display = ("product_id", "label", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("product_id", "label")


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    """Admin interface for the Purchase model.

    Purchases are only ever written by verification/claim flows, so the
    admin is read-only — staff can look up a transaction, not edit it.
    """

    list_display = (
        "id",
        "platform",
        "product",
        "store_transaction_id",
        "user",
        "status",
        "environment",
        "verified_at",
    )
    list_filter = ("platform", "status", "environment")
    search_fields = ("store_transaction_id", "device_id", "user__email")
    readonly_fields: ClassVar[tuple[str, ...]] = (
        "platform",
        "product",
        "store_transaction_id",
        "purchase_token",
        "user",
        "device_id",
        "status",
        "amount",
        "currency",
        "environment",
        "raw_response",
        "verified_at",
    )

    def has_add_permission(self, request: HttpRequest) -> bool:  # noqa: PLR6301
        """Disallow creating purchases by hand from the admin."""
        return False

    def has_change_permission(  # noqa: PLR6301
        self, request: HttpRequest, obj: Purchase | None = None
    ) -> bool:
        """Disallow editing purchases from the admin."""
        return False

    def has_delete_permission(  # noqa: PLR6301
        self, request: HttpRequest, obj: Purchase | None = None
    ) -> bool:
        """Disallow deleting purchases from the admin."""
        return False
