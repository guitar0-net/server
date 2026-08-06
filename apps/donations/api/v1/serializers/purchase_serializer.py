# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Serializer for the purchase verification response payload."""

from rest_framework import serializers

from apps.donations.models import Purchase


class PurchaseSerializer(serializers.ModelSerializer[Purchase]):
    """Serialize a verified purchase back to the client."""

    product_id = serializers.CharField(source="product.product_id", read_only=True)

    class Meta:
        """Metadata for PurchaseSerializer."""

        model = Purchase
        fields = ("platform", "product_id", "status", "verified_at")
        read_only_fields = ("platform", "status", "verified_at")
