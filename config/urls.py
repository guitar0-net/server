# SPDX-FileCopyrightText: 2025-2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/

Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path("admin-guitar0/", admin.site.urls),
    path("api/v1/", include("apps.accounts.api.v1.urls")),
    path("api/v1/", include("apps.chords.api.v1.urls")),
    path("api/v1/", include("apps.lessons.api.v1.urls")),
    path("api/v1/", include("apps.songs.api.v1.urls")),
    path("api/v1/", include("apps.courses.api.v1.urls")),
    path("api/v1/", include("apps.announcements.api.v1.urls")),
    path("api/v1/", include("apps.sync.api.v1.urls")),
    path("api/v1/", include("apps.donations.api.v1.urls")),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/v1/docs/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    path("metrics/", include("apps.ops.urls")),
    path("markdownx/", include("markdownx.urls")),
]

if settings.DEBUG:
    urlpatterns += [
        path(
            "api/v1/docs/swagger/",
            SpectacularSwaggerView.as_view(url_name="schema"),
            name="swagger-ui",
        ),
    ]
