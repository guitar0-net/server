# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Serializer for the purchase verification error payload."""

from rest_framework import serializers

from apps.donations.constants import VerifyErrorCode


class VerifyErrorSerializer(serializers.Serializer[None]):
    """Describes the error body PurchaseVerifyView returns.

    Documentation-only: it exists so drf-spectacular publishes `code` and its
    permitted values, without which a generated client has to hard-code the
    strings it is meant to branch on. Never used to build or parse a payload.
    """

    detail = serializers.CharField(read_only=True)
    code = serializers.ChoiceField(
        choices=[(code.value, code.name) for code in VerifyErrorCode], read_only=True
    )
