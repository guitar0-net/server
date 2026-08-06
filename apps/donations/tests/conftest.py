# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Pytest fixtures for testing the donations app."""

import pytest
from django.core.cache import cache as django_cache
from rest_framework.test import APIClient

from apps.donations.models import DonationProduct, Purchase
from apps.donations.tests.factories import DonationProductFactory, PurchaseFactory


@pytest.fixture(autouse=True)
def _clear_throttle_cache() -> None:
    """Reset DRF's throttle counters between tests.

    They live in Django's cache, which pytest-django does not reset the way
    it resets the database — without this, PurchaseVerifyView's 5/minute
    scope leaks across tests sharing the same client IP.
    """
    django_cache.clear()


@pytest.fixture
def donation_product() -> DonationProduct:
    """Fixture creating an active donation product for testing."""
    return DonationProductFactory.create()


@pytest.fixture
def purchase() -> Purchase:
    """Fixture creating a completed purchase for testing."""
    return PurchaseFactory.create()


@pytest.fixture
def api_client() -> APIClient:
    """Return an unauthenticated DRF API client."""
    return APIClient()
