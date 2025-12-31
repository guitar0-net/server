# SPDX-FileCopyrightText: 2025 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Url config for the chords app."""

from rest_framework.routers import DefaultRouter

from .views import ChordViewSet

router = DefaultRouter()
router.register(
    r"chords",
    ChordViewSet,
    basename="chord",
)

urlpatterns = router.urls
