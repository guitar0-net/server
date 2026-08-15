# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Admin settings for songs."""

from django.contrib import admin
from django.db.models import QuerySet
from django.forms import ModelForm
from django.http import HttpRequest
from markdownx.admin import MarkdownxModelAdmin  # type: ignore[import-untyped]

from apps.songs.models import Song
from apps.songs.services import delete_song, delete_songs, save_song


@admin.register(Song)
class SongAdmin(MarkdownxModelAdmin):  # type: ignore[misc]
    """Admin interface for the Song model."""

    filter_horizontal = ("chords", "schemes")
    list_display = ("title", "metronome")
    list_editable = ("metronome",)

    def save_model(  # noqa: PLR6301
        self,
        request: HttpRequest,
        obj: Song,
        form: ModelForm[Song],
        change: bool,
    ) -> None:
        """Save the song and propagate the change timestamp to related lessons."""
        save_song(obj)

    def delete_model(self, request: HttpRequest, obj: Song) -> None:  # noqa: PLR6301
        """Delete a song and propagate the change to lessons that used it."""
        delete_song(obj)

    def delete_queryset(  # noqa: PLR6301
        self,
        request: HttpRequest,
        queryset: QuerySet[Song],
    ) -> None:
        """Delete the songs selected in the bulk action.

        Django does not route the bulk action through `delete_model`, so the
        propagation has to be repeated here or deleting from the changelist
        would leave every affected lesson stale.
        """
        delete_songs(queryset)
