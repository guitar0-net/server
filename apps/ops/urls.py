# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""URL configuration for ops app."""

from django.urls import path

from .views import health_view, metrics_view, ready_view

app_name = "ops"

urlpatterns = [
    path("metrics/", metrics_view, name="prometheus"),
    path("health/", health_view, name="health"),
    path("ready/", ready_view, name="ready"),
]
