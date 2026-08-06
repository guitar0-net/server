# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Views for the donations API v1."""

import logging

from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.accounts.models.user import User
from apps.donations.constants import DONATION_VERIFY_THROTTLE_SCOPE
from apps.donations.models import DonationProduct
from apps.donations.selectors import get_active_donation_products
from apps.donations.services import (
    PurchaseVerificationError,
    StoreCommunicationError,
    UnknownDonationProductError,
    claim_device_purchases,
    verify_and_record_purchase,
)

from .serializers.claim_device_request_serializer import ClaimDeviceRequestSerializer
from .serializers.donation_product_list_serializer import DonationProductListSerializer
from .serializers.purchase_serializer import PurchaseSerializer
from .serializers.purchase_verify_request_serializer import (
    PurchaseVerifyRequestSerializer,
)

logger = logging.getLogger("donations")


class DonationProductListView(ListAPIView[DonationProduct]):
    """List active donation products clients can offer for purchase."""

    permission_classes = (AllowAny,)
    serializer_class = DonationProductListSerializer

    def get_queryset(self) -> QuerySet[DonationProduct]:  # noqa: PLR6301
        """Return active donation products."""
        return get_active_donation_products()


@extend_schema(responses=PurchaseSerializer)
class PurchaseVerifyView(APIView):
    """Verify a store purchase and record it.

    Unauthenticated so a donation can happen before login (the mobile app is
    offline-first); if the caller is authenticated, the purchase is
    attributed to them directly — otherwise it's tagged with `device_id` for
    later claiming.
    """

    permission_classes = (AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = DONATION_VERIFY_THROTTLE_SCOPE

    def post(self, request: Request) -> Response:  # noqa: PLR6301
        """Validate the purchase payload and verify it against the store."""
        serializer = PurchaseVerifyRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user: User | None = None
        if request.user.is_authenticated:
            assert isinstance(request.user, User)
            user = request.user

        try:
            purchase = verify_and_record_purchase(
                platform=data["platform"],
                product_id=data["product_id"],
                store_transaction_id=data["store_transaction_id"],
                purchase_token=data["purchase_token"],
                signed_transaction_info=data["signed_transaction_info"],
                user=user,
                device_id=data["device_id"],
            )
        except UnknownDonationProductError:
            logger.info("Rejected donation verify: unknown product_id")
            return Response(
                {"detail": "Unknown product_id."}, status=status.HTTP_400_BAD_REQUEST
            )
        except PurchaseVerificationError as exc:
            logger.info("Rejected donation verify: %s", exc)
            return Response(
                {"detail": str(exc)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        except StoreCommunicationError as exc:
            logger.warning("Store unreachable during donation verify: %s", exc)
            return Response(
                {"detail": "Store unavailable, please retry."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(PurchaseSerializer(purchase).data)


class ClaimDeviceDonationsView(APIView):
    """Attach a device's anonymous donations to the authenticated user.

    Meant to be called once after login so a donation made anonymously on
    the same device before signing in doesn't require a store-side restore.
    """

    permission_classes = (IsAuthenticated,)

    def post(self, request: Request) -> Response:  # noqa: PLR6301
        """Claim all unclaimed purchases for the given device_id."""
        serializer = ClaimDeviceRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        assert isinstance(request.user, User)
        claimed = claim_device_purchases(
            request.user, serializer.validated_data["device_id"]
        )
        return Response({"claimed": claimed})
