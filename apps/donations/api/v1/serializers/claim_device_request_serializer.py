# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Serializer for the claim-device request payload."""

from rest_framework import serializers


class ClaimDeviceRequestSerializer(serializers.Serializer[None]):
    """Validates the device_id whose anonymous purchases should be claimed."""

    device_id = serializers.CharField(max_length=64)
