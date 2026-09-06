# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Serializer for the purchase verification request payload."""

from typing import Any

from rest_framework import serializers

from apps.donations.constants import Platform


class PurchaseVerifyRequestSerializer(serializers.Serializer[None]):
    """Validates a client's request to verify a store purchase.

    `purchase_token` is required for Android (needed again to acknowledge)
    and unused for iOS. `signed_transaction_info` is required for iOS (the
    JWS StoreKit hands the client for its own transaction) and unused for
    Android. `store_transaction_id` is required for iOS but optional for
    Android: Google leaves `orderId` unset until a pending payment clears,
    so an Android client reporting a purchase it saw as PENDING has no id to
    send and would otherwise be refused here instead of being told to retry.
    `device_id` is only used when the request is unauthenticated.
    """

    platform = serializers.ChoiceField(choices=Platform.choices)
    product_id = serializers.CharField(max_length=100)
    store_transaction_id = serializers.CharField(
        required=False, allow_blank=True, default="", max_length=255
    )
    purchase_token = serializers.CharField(required=False, allow_blank=True, default="")
    signed_transaction_info = serializers.CharField(
        required=False, allow_blank=True, default=""
    )
    device_id = serializers.CharField(
        required=False, allow_blank=True, default="", max_length=64
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:  # noqa: PLR6301
        """Require the platform-specific proof each store needs to verify."""
        if attrs["platform"] == Platform.ANDROID and not attrs["purchase_token"]:
            raise serializers.ValidationError({
                "purchase_token": "Required when platform is android."
            })
        if attrs["platform"] == Platform.IOS and not attrs["signed_transaction_info"]:
            raise serializers.ValidationError({
                "signed_transaction_info": "Required when platform is ios."
            })
        if attrs["platform"] == Platform.IOS and not attrs["store_transaction_id"]:
            raise serializers.ValidationError({
                "store_transaction_id": "Required when platform is ios."
            })
        return attrs
