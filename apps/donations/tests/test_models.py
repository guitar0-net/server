# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for DonationProduct and Purchase models."""

import pytest
from django.db import IntegrityError

from apps.accounts.tests.factories.user import UserFactory
from apps.donations.constants import Platform
from apps.donations.tests.factories import DonationProductFactory, PurchaseFactory


@pytest.mark.django_db
def test_donation_product_str_returns_its_product_id() -> None:
    product = DonationProductFactory.create(product_id="thank_you_щедро")

    assert str(product) == "thank_you_щедро"


@pytest.mark.django_db
def test_purchase_str_includes_platform_and_transaction_id() -> None:
    purchase = PurchaseFactory.create(
        platform=Platform.IOS, store_transaction_id="2000000123456789"
    )

    assert str(purchase) == "ios:2000000123456789"


@pytest.mark.django_db
def test_purchase_rejects_duplicate_transaction_id_for_same_platform() -> None:
    PurchaseFactory.create(
        platform=Platform.ANDROID,
        store_transaction_id="dup-id",
        user=UserFactory.create(email="виктор@example.com"),
    )

    with pytest.raises(IntegrityError):
        PurchaseFactory.create(
            platform=Platform.ANDROID,
            store_transaction_id="dup-id",
            user=UserFactory.create(email="галина@example.com"),
        )


@pytest.mark.django_db
def test_purchase_allows_same_transaction_id_on_different_platforms() -> None:
    PurchaseFactory.create(
        platform=Platform.ANDROID,
        store_transaction_id="shared-id",
        user=UserFactory.create(email="анна@example.com"),
    )

    purchase = PurchaseFactory.create(
        platform=Platform.IOS,
        store_transaction_id="shared-id",
        user=UserFactory.create(email="борис@example.com"),
    )

    assert purchase.pk is not None


@pytest.mark.django_db
def test_purchase_survives_its_users_deletion() -> None:
    purchase = PurchaseFactory.create()
    user = purchase.user
    assert user is not None

    user.delete()
    purchase.refresh_from_db()

    assert purchase.user is None
