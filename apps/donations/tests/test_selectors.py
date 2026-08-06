# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for donations selectors."""

import pytest

from apps.accounts.tests.factories.user import UserFactory
from apps.donations.constants import Platform
from apps.donations.selectors import (
    get_active_donation_products,
    get_donation_product,
    get_purchase,
    get_unclaimed_purchases_for_device,
)
from apps.donations.tests.factories import DonationProductFactory, PurchaseFactory


@pytest.mark.django_db
def test_get_active_donation_products_excludes_inactive() -> None:
    DonationProductFactory.create(product_id="active-один", is_active=True)
    DonationProductFactory.create(product_id="inactive-два", is_active=False)

    products = get_active_donation_products()

    assert [p.product_id for p in products] == ["active-один"]


@pytest.mark.django_db
def test_get_donation_product_finds_a_deactivated_product_too() -> None:
    """Reconciling an already-recorded purchase must survive its product being retired.

    See apps.donations.services.verify_and_record_purchase for where "is this
    still sellable to a new buyer" is actually enforced.
    """
    DonationProductFactory.create(product_id="retired-tier", is_active=False)

    result = get_donation_product("retired-tier")

    assert result is not None


@pytest.mark.django_db
def test_get_donation_product_returns_none_for_an_unknown_product_id() -> None:
    result = get_donation_product("не-существует")

    assert result is None


@pytest.mark.django_db
def test_get_donation_product_finds_active_product_by_id() -> None:
    DonationProductFactory.create(product_id="щедрое-спасибо", is_active=True)

    result = get_donation_product("щедрое-спасибо")

    assert result is not None


@pytest.mark.django_db
def test_get_purchase_finds_by_platform_and_transaction_id() -> None:
    PurchaseFactory.create(platform=Platform.IOS, store_transaction_id="tx-42")

    result = get_purchase(Platform.IOS, "tx-42")

    assert result is not None


@pytest.mark.django_db
def test_get_purchase_does_not_match_a_different_platform() -> None:
    PurchaseFactory.create(platform=Platform.ANDROID, store_transaction_id="tx-99")

    result = get_purchase(Platform.IOS, "tx-99")

    assert result is None


@pytest.mark.django_db
def test_get_unclaimed_purchases_for_device_excludes_claimed_ones() -> None:
    user = UserFactory.create()
    PurchaseFactory.create(device_id="device-a", user=None)
    PurchaseFactory.create(device_id="device-a", user=user)

    result = get_unclaimed_purchases_for_device("device-a")

    assert result.count() == 1
