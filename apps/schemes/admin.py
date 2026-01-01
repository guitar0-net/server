# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later


"""Admin settings for schemes."""

from django.contrib import admin

from apps.schemes.models import ImageScheme


@admin.register(ImageScheme)
class ImageSchemeAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    """Admin interface for the ImageScheme model."""

    list_display = ("code", "inscription", "image")
    search_fields = ("code", "inscription")
