# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for lessons services."""

from datetime import UTC, datetime

import pytest

from apps.chords.tests.factories import ChordFactory
from apps.lessons.models import Lesson
from apps.lessons.services import (
    touch_lessons_for_chords,
    touch_lessons_for_schemes,
    touch_lessons_for_songs,
)
from apps.lessons.tests.factories import LessonFactory
from apps.schemes.tests.factories import ImageSchemeFactory
from apps.songs.tests.factories import SongFactory


@pytest.mark.django_db
def test_touch_lessons_for_songs_stamps_lessons_holding_the_song() -> None:
    stale = datetime(2026, 2, 3, tzinfo=UTC)
    song = SongFactory.create(title="Пісня «Зоря» — тест")
    lesson = LessonFactory.create(songs=[song])
    Lesson.objects.filter(pk=lesson.pk).update(updated_at=stale)

    touch_lessons_for_songs([song.pk])

    lesson.refresh_from_db()
    assert lesson.updated_at > stale


@pytest.mark.django_db
def test_touch_lessons_for_chords_stamps_lessons_that_reach_the_chord() -> None:
    stale = datetime(2026, 2, 4, tzinfo=UTC)
    chord = ChordFactory.create(title="Am7♭5")
    song = SongFactory.create(title="Ліхтарі", chords=[chord])
    lesson = LessonFactory.create(songs=[song])
    Lesson.objects.filter(pk=lesson.pk).update(updated_at=stale)

    touch_lessons_for_chords([chord.pk])

    lesson.refresh_from_db()
    assert lesson.updated_at > stale


@pytest.mark.django_db
def test_touch_lessons_for_chords_leaves_lessons_without_that_chord_alone() -> None:
    stale = datetime(2026, 2, 5, tzinfo=UTC)
    chord = ChordFactory.create(title="F♯dim")
    LessonFactory.create(songs=[SongFactory.create(title="Смерека", chords=[chord])])
    untouched = LessonFactory.create(songs=[SongFactory.create(title="Веснянка")])
    Lesson.objects.filter(pk=untouched.pk).update(updated_at=stale)

    touch_lessons_for_chords([chord.pk])

    untouched.refresh_from_db()
    assert untouched.updated_at == stale


@pytest.mark.django_db
def test_touch_lessons_for_chords_stamps_a_lesson_once_despite_repeated_joins() -> None:
    stale = datetime(2026, 2, 6, tzinfo=UTC)
    chords = ChordFactory.create_batch(3)
    song = SongFactory.create(title="Ой у лузі", chords=chords)
    lesson = LessonFactory.create(songs=[song])
    Lesson.objects.filter(pk=lesson.pk).update(updated_at=stale)

    stamped = touch_lessons_for_chords([chord.pk for chord in chords])

    assert stamped == 1


@pytest.mark.django_db
def test_touch_lessons_for_schemes_stamps_lessons_reaching_the_scheme() -> None:
    stale = datetime(2026, 2, 7, tzinfo=UTC)
    scheme = ImageSchemeFactory.create(inscription="Бій «шістка»")
    song = SongFactory.create(title="Криниця", schemes=[scheme])
    lesson = LessonFactory.create(songs=[song])
    Lesson.objects.filter(pk=lesson.pk).update(updated_at=stale)

    touch_lessons_for_schemes([scheme.pk])

    lesson.refresh_from_db()
    assert lesson.updated_at > stale


@pytest.mark.django_db
def test_touch_lessons_for_chords_stamps_nothing_when_given_no_chords() -> None:
    LessonFactory.create(songs=[SongFactory.create(title="Дощ у місті")])

    stamped = touch_lessons_for_chords([])

    assert stamped == 0
