# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Services for the songs app."""

from django.db import transaction
from django.db.models import QuerySet

from apps.lessons.services import touch_lessons_for_songs
from apps.songs.models import Song


@transaction.atomic
def save_song(song: Song) -> None:
    """Persist a Song instance and propagate the change to related lessons.

    All Song mutations must go through this function — calling song.save()
    directly bypasses the propagation and leaves Lesson.updated_at stale.

    Propagation updates `updated_at` on every Lesson that uses this song so
    that the sync endpoint reflects content changes originating in a song.
    """
    song.save()
    touch_lessons_for_songs([song.pk])


@transaction.atomic
def delete_song(song: Song) -> None:
    """Delete a Song instance, propagating to related lessons first.

    The lesson-to-song rows that identify the affected lessons are removed
    along with the song, so they must be read before the delete.
    """
    if song.pk is not None:
        touch_lessons_for_songs([song.pk])
        song.delete()


@transaction.atomic
def delete_songs(songs: QuerySet[Song]) -> None:
    """Delete every song in the queryset, propagating to related lessons.

    Serves the admin bulk action, which never routes through `delete_song`.
    """
    touch_lessons_for_songs(list(songs.values_list("pk", flat=True)))
    songs.delete()
