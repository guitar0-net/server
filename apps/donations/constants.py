# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Constants for the donations app."""

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


# Separate, stricter throttle scope for donations/verify: unlike the rest of
# the anonymous-accessible API, each call pays for an outbound request to
# Google Play or the App Store Server API, so the shared AnonRateThrottle
# rate is too generous here.
DONATION_VERIFY_THROTTLE_SCOPE = "donation_verify"
