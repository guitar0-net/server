# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later


"""Admin settings for schemes."""

from django.contrib import admin
from django.db.models import QuerySet
from django.forms import ModelForm
from django.http import HttpRequest

from apps.schemes.models import ImageScheme
from apps.schemes.services import ImageSchemeService


@admin.register(ImageScheme)
class ImageSchemeAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    """Admin interface for the ImageScheme model."""

    list_display = ("code", "inscription", "image")
    search_fields = ("code", "inscription")

    def save_model(  # noqa: PLR6301
        self,
        request: HttpRequest,
        obj: ImageScheme,
        form: ModelForm[ImageScheme],
        change: bool,
    ) -> None:
        """Save the scheme and propagate the change timestamp to related lessons."""
        ImageSchemeService.save_image_scheme(scheme=obj)

    def delete_model(  # noqa: PLR6301
        self,
        request: HttpRequest,
        obj: ImageScheme,
    ) -> None:
        """Delete a scheme and propagate the change to lessons that used it."""
        ImageSchemeService.delete_image_scheme(scheme=obj)

    def delete_queryset(  # noqa: PLR6301
        self,
        request: HttpRequest,
        queryset: QuerySet[ImageScheme],
    ) -> None:
        """Delete the schemes selected in the bulk action.

        Django does not route the bulk action through `delete_model`, so the
        propagation has to be repeated here or deleting from the changelist
        would leave every affected lesson stale.
        """
        ImageSchemeService.delete_image_schemes(schemes=queryset)
