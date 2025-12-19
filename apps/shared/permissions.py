# SPDX-FileCopyrightText: 2025 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Custom permissions."""

from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


class IsStaffOrReadOnly(BasePermission):
    """Allow read-only access for everyone, write access for staff only."""

    def has_permission(self, request: Request, view: APIView) -> bool:  # noqa: PLR6301
        """Check if the request should be permitted.

        Args:
            request: The incoming request
            view: The view being accessed

        Returns:
            bool: True if request is allowed, False otherwise
        """
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)
