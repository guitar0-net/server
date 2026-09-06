# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Constants for the donations app."""

from enum import IntEnum, StrEnum

from django.db import models


class Platform(models.TextChoices):
    """Store a purchase was made through."""

    ANDROID = "android", "Android"
    IOS = "ios", "iOS"


class PurchaseStatus(models.TextChoices):
    """Lifecycle status of a recorded purchase.

    REFUNDED and REVOKED are not written by anything yet — recognizing a
    refund requires either a store webhook or a reconciliation job, neither
    of which exists in this iteration. They exist now purely so that
    capability can be added later without a schema migration.
    """

    VERIFIED = "verified", "Подтверждено стором"
    COMPLETED = "completed", "Завершено"
    REFUNDED = "refunded", "Возвращено"
    REVOKED = "revoked", "Отозвано"


class GooglePlayPurchaseState(IntEnum):
    """`purchaseState` of Google's ProductPurchase resource.

    Only PURCHASED may be recorded as a donation, but the two rejected states
    pull in opposite directions and must not be collapsed: a PENDING payment
    can still clear and has to be retried, while a CANCELED one never will.
    """

    PURCHASED = 0
    CANCELED = 1
    PENDING = 2


class VerifyErrorCode(StrEnum):
    """Machine-readable reason the verify endpoint refused a purchase.

    Sent next to the human-readable `detail` so a client can branch on the
    outcome without parsing prose, which is free to be reworded at any time.
    """

    UNKNOWN_PRODUCT = "unknown_product"
    PURCHASE_PENDING = "purchase_pending"
    PURCHASE_REJECTED = "purchase_rejected"
    STORE_UNAVAILABLE = "store_unavailable"


# Separate, stricter throttle scope for donations/verify: unlike the rest of
# the anonymous-accessible API, each call pays for an outbound request to
# Google Play or the App Store Server API, so the shared AnonRateThrottle
# rate is too generous here.
DONATION_VERIFY_THROTTLE_SCOPE = "donation_verify"
