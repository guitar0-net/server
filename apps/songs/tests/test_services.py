# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for songs services."""

from datetime import UTC, datetime

import pytest

from apps.lessons.models import Lesson
from apps.lessons.tests.factories import LessonFactory
from apps.songs.models import Song
from apps.songs.services import delete_song, delete_songs, save_song
from apps.songs.tests.factories import SongFactory


@pytest.mark.django_db
def test_save_song_persists_changes_to_the_database() -> None:
    song = SongFactory.create()
    song.title = "Обновлённое название"

    save_song(song)

    song.refresh_from_db()
    assert song.title == "Обновлённое название"


@pytest.mark.django_db
def test_save_song_propagates_updated_at_to_related_lessons() -> None:
    old_ts = datetime(2026, 1, 1, tzinfo=UTC)
    song = SongFactory.create()
    lesson = LessonFactory.create(songs=[song])
    Lesson.objects.filter(pk=lesson.pk).update(updated_at=old_ts)

    save_song(song)

    lesson.refresh_from_db()
    assert lesson.updated_at > old_ts


@pytest.mark.django_db
def test_save_song_does_not_affect_unrelated_lessons() -> None:
    old_ts = datetime(2026, 1, 1, tzinfo=UTC)
    song = SongFactory.create()
    unrelated = LessonFactory.create()
    Lesson.objects.filter(pk=unrelated.pk).update(updated_at=old_ts)

    save_song(song)

    unrelated.refresh_from_db()
    assert unrelated.updated_at == old_ts


@pytest.mark.django_db
def test_delete_song_stamps_lessons_before_the_relation_disappears() -> None:
    stale = datetime(2026, 1, 2, tzinfo=UTC)
    song = SongFactory.create(title="Стежка до моря")
    lesson = LessonFactory.create(songs=[song])
    Lesson.objects.filter(pk=lesson.pk).update(updated_at=stale)

    delete_song(song)

    lesson.refresh_from_db()
    assert lesson.updated_at > stale


@pytest.mark.django_db
def test_delete_songs_stamps_lessons_before_the_relation_disappears() -> None:
    stale = datetime(2026, 1, 3, tzinfo=UTC)
    lesson = LessonFactory.create(songs=[SongFactory.create(title="Зорі над Дністром")])
    Lesson.objects.filter(pk=lesson.pk).update(updated_at=stale)

    delete_songs(Song.objects.all())

    lesson.refresh_from_db()
    assert lesson.updated_at > stale
