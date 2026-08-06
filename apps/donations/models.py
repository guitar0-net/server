# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Models for the donations app."""

from typing import ClassVar

from django.conf import settings
from django.db import models

from apps.donations.constants import Platform, PurchaseStatus


class DonationProduct(models.Model):
    """A non-consumable donation SKU, using the same product_id on both stores.

    The store — not this table — is the source of truth for price, currency
    and localized title; those are resolved by the mobile client directly
    against Google Play / the App Store using the product_id. This table only
    tracks which SKUs currently exist and are sellable, so new donation tiers
    can be added from the admin without an app release.
    """

    product_id = models.CharField("Идентификатор товара", max_length=100, unique=True)
    label = models.CharField(
        "Название",
        max_length=100,
        help_text="Только для админки, пользователю не показывается",
    )
    is_active = models.BooleanField("Активен", default=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        verbose_name = "Донат-товар"
        verbose_name_plural = "Донат-товары"
        ordering: ClassVar[list[str]] = ["product_id"]

    def __str__(self) -> str:
        return self.product_id


class Purchase(models.Model):
    """A store transaction verified for a donation product.

    `user` is nullable because the mobile app is offline-first and lets a
    donation happen before login: an anonymous purchase is recorded against
    `device_id` (a UUID the client generates and persists itself) and later
    attached to a user, either explicitly via the claim-device endpoint, or
    implicitly when the same store transaction_id is re-submitted while
    authenticated (the restore-purchases flow after a reinstall).
    """

    platform = models.CharField("Платформа", max_length=10, choices=Platform.choices)
    product = models.ForeignKey(
        DonationProduct,
        verbose_name="Товар",
        on_delete=models.PROTECT,
        related_name="purchases",
    )
    store_transaction_id = models.CharField("ID транзакции в сторе", max_length=255)
    purchase_token = models.TextField(
        "Токен покупки (Android)",
        blank=True,
        default="",
        help_text="Нужен повторно для acknowledge; для iOS не используется",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Пользователь",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="purchases",
    )
    device_id = models.CharField(
        "ID устройства (анонимно)",
        max_length=64,
        blank=True,
        default="",
        help_text="Заполнено, только пока покупка не привязана к пользователю",
    )
    status = models.CharField(
        "Статус",
        max_length=10,
        choices=PurchaseStatus.choices,
        default=PurchaseStatus.VERIFIED,
    )
    amount = models.DecimalField(
        "Сумма", max_digits=10, decimal_places=2, null=True, blank=True
    )
    currency = models.CharField("Валюта", max_length=3, blank=True, default="")
    environment = models.CharField(
        "Окружение стора",
        max_length=20,
        blank=True,
        default="",
        help_text=(
            "Apple's Sandbox/Production/Xcode/LocalTesting from the verified "
            "transaction. Apple explicitly falls back to verifying Sandbox "
            "transactions in production for App Review, so this is how staff "
            "tell a real donation from a free sandbox one. Left blank for "
            "Android, which has no equivalent concept on this endpoint."
        ),
    )
    raw_response = models.JSONField("Сырой ответ стора", default=dict, blank=True)
    verified_at = models.DateTimeField("Подтверждено", auto_now_add=True)

    class Meta:
        verbose_name = "Покупка (донат)"
        verbose_name_plural = "Покупки (донаты)"
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["platform", "store_transaction_id"],
                name="unique_platform_transaction",
            )
        ]
        ordering: ClassVar[list[str]] = ["-verified_at"]

    def __str__(self) -> str:
        return f"{self.platform}:{self.store_transaction_id}"
