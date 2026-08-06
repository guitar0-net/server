# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Serializer for listing active donation products."""

from rest_framework import serializers

from apps.donations.models import DonationProduct


class DonationProductListSerializer(serializers.ModelSerializer[DonationProduct]):
    """Expose only the product_id field.

    Price and title are resolved by the client directly against the store's
    own SDK using this id — they are deliberately not duplicated here.
    """

    class Meta:
        """Metadata for DonationProductListSerializer."""

        model = DonationProduct
        fields = ("product_id",)
