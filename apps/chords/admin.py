# SPDX-FileCopyrightText: 2025 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Admin settings for chords."""

from __future__ import annotations

from typing import Any, ClassVar

from django.contrib import admin
from django.contrib.admin.options import InlineModelAdmin
from django.db.models import QuerySet
from django.forms import ModelForm
from django.http import HttpRequest

from apps.chords.models import Chord, ChordPosition
from apps.chords.services import ChordService


class ChordPositionInline(admin.TabularInline):  # type: ignore[type-arg]
    """Admin interface for ChordPosition."""

    model = ChordPosition
    extra = 0
    fields = ("string_number", "fret", "finger")


@admin.register(Chord)
class ChordAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    """Admin interface for the Chord model."""

    list_display = ("title", "musical_title", "start_fret", "has_barre")
    list_filter = ("has_barre",)
    search_fields = ("title", "musical_title")
    ordering = ("order_in_note",)
    inlines: ClassVar[list[type[InlineModelAdmin[Any, Any]]]] = [ChordPositionInline]

    def save_model(
        self,
        request: HttpRequest,
        obj: Chord,
        form: ModelForm[Chord],
        change: bool,
    ) -> None:
        """Leave an edited chord unwritten until `save_related` runs.

        `ChordService.save_chord` decides whether to propagate by comparing the
        stored row against what the save produces, so the row must still hold
        the pre-edit values when it runs — and it can only run once the
        position inlines are saved, since the SVG is rendered from them. A new
        chord is written here regardless: the inline formsets need its pk.
        """
        if not change:
            super().save_model(request, obj, form, change)

    def save_related(
        self,
        request: HttpRequest,
        form: ModelForm[Chord],
        formsets: Any,  # noqa: ANN401
        change: bool,
    ) -> None:
        """Persist the chord and its regenerated SVG once the inlines are saved."""
        super().save_related(request, form, formsets, change)
        ChordService.save_chord(chord=form.instance)

    def delete_model(self, request: HttpRequest, obj: Chord) -> None:  # noqa: PLR6301
        """Delete a chord and propagate the change to lessons that used it."""
        ChordService.delete_chord(chord=obj)

    def delete_queryset(  # noqa: PLR6301
        self,
        request: HttpRequest,
        queryset: QuerySet[Chord],
    ) -> None:
        """Delete the chords selected in the bulk action.

        Django does not route the bulk action through `delete_model`, so the
        propagation has to be repeated here or deleting from the changelist
        would leave every affected lesson stale.
        """
        ChordService.delete_chords(chords=queryset)
