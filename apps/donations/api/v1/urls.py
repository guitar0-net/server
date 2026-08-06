# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""URL configuration for donations API v1."""

from django.urls import path

from .views import ClaimDeviceDonationsView, DonationProductListView, PurchaseVerifyView

urlpatterns = [
    path(
        "donations/products/",
        DonationProductListView.as_view(),
        name="donation-products",
    ),
    path("donations/verify/", PurchaseVerifyView.as_view(), name="donation-verify"),
    path("donations/claim/", ClaimDeviceDonationsView.as_view(), name="donation-claim"),
]
