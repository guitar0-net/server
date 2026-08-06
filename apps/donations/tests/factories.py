# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Factories for generating test donations instances."""

from factory import Faker, Sequence, SubFactory  # type: ignore[attr-defined]
from factory.django import DjangoModelFactory

from apps.accounts.tests.factories.user import UserFactory
from apps.donations.constants import Platform, PurchaseStatus
from apps.donations.models import DonationProduct, Purchase


class DonationProductFactory(DjangoModelFactory[DonationProduct]):
    """Factory for creating DonationProduct instances."""

    product_id = Sequence(lambda n: f"thank_you_{n}")
    label = Faker("word")
    is_active = True

    class Meta:
        """Metadata for DonationProductFactory."""

        model = DonationProduct


class PurchaseFactory(DjangoModelFactory[Purchase]):
    """Factory for creating Purchase instances."""

    platform = Platform.ANDROID
    product = SubFactory(DonationProductFactory)
    store_transaction_id = Sequence(lambda n: f"GPA.{n:04d}")
    purchase_token = Faker("uuid4")
    user = SubFactory(UserFactory)
    device_id = ""
    status = PurchaseStatus.COMPLETED

    class Meta:
        """Metadata for PurchaseFactory."""

        model = Purchase
