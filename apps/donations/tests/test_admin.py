# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for donations admin."""

import pytest
from django.contrib.admin.sites import AdminSite
from django.http import HttpRequest

from apps.donations.admin import PurchaseAdmin
from apps.donations.models import Purchase
from apps.donations.tests.factories import PurchaseFactory


def test_purchase_admin_forbids_adding_purchases_by_hand() -> None:
    can_add = PurchaseAdmin(Purchase, AdminSite()).has_add_permission(HttpRequest())

    assert can_add is False


@pytest.mark.django_db
def test_purchase_admin_forbids_editing_an_existing_purchase() -> None:
    purchase = PurchaseFactory.create()

    can_change = PurchaseAdmin(Purchase, AdminSite()).has_change_permission(
        HttpRequest(), obj=purchase
    )

    assert can_change is False


@pytest.mark.django_db
def test_purchase_admin_forbids_deleting_an_existing_purchase() -> None:
    purchase = PurchaseFactory.create()

    can_delete = PurchaseAdmin(Purchase, AdminSite()).has_delete_permission(
        HttpRequest(), obj=purchase
    )

    assert can_delete is False
