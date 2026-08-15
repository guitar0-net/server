# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Services for the lessons app."""

from collections.abc import Iterable

from django.db.models import QuerySet
from django.utils import timezone

from apps.lessons.models import Lesson


def touch_lessons_for_songs(song_ids: Iterable[int]) -> int:
    """Bump `updated_at` on every lesson that contains one of the given songs."""
    return _touch(Lesson.objects.filter(songs__in=list(song_ids)))


def touch_lessons_for_chords(chord_ids: Iterable[int]) -> int:
    """Bump `updated_at` on every lesson whose songs use one of the given chords.

    Editing a chord changes its rendered SVG, which is part of both the sync
    payload and the printed PDF. Without this propagation the delta sync filter
    (`Lesson.updated_at__gt=since`) matches nothing and clients keep the old
    diagram indefinitely.
    """
    return _touch(Lesson.objects.filter(songs__chords__in=list(chord_ids)))


def touch_lessons_for_schemes(scheme_ids: Iterable[int]) -> int:
    """Bump `updated_at` on every lesson whose songs use one of the given schemes.

    Same reasoning as `touch_lessons_for_chords` — replacing a scheme image
    changes rendered output without touching any lesson row on its own.
    """
    return _touch(Lesson.objects.filter(songs__schemes__in=list(scheme_ids)))


def _touch(lessons: QuerySet[Lesson]) -> int:
    """Stamp the matched lessons with the current time, returning the row count.

    Filtering through a many-to-many relation yields duplicate rows, so the
    match is narrowed to primary keys before updating. `queryset.update()` is
    deliberate: it avoids N+1 saves and writes `updated_at` despite `auto_now`,
    which would otherwise ignore the assignment.
    """
    return Lesson.objects.filter(pk__in=lessons.values("pk")).update(
        updated_at=timezone.now()
    )
