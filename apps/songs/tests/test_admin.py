# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for songs admin."""

from datetime import UTC, datetime

import pytest
from django.contrib.admin.sites import AdminSite
from django.forms.models import modelform_factory
from django.test import RequestFactory

from apps.lessons.models import Lesson
from apps.lessons.tests.factories import LessonFactory
from apps.songs.admin import SongAdmin
from apps.songs.models import Song
from apps.songs.tests.factories import SongFactory


@pytest.mark.django_db
def test_song_admin_save_model_propagates_updated_at_to_related_lessons() -> None:
    old_ts = datetime(2026, 1, 1, tzinfo=UTC)
    song = SongFactory.create()
    lesson = LessonFactory.create(songs=[song], updated_at=old_ts)
    form = modelform_factory(Song, fields=("title",))(instance=song)

    SongAdmin(Song, AdminSite()).save_model(
        request=RequestFactory().post("/"), obj=song, form=form, change=False
    )

    lesson.refresh_from_db()
    assert lesson.updated_at > old_ts


@pytest.mark.django_db
def test_song_admin_delete_model_propagates_updated_at_to_related_lessons() -> None:
    stale = datetime(2026, 6, 5, tzinfo=UTC)
    song = SongFactory.create(title="Остання електричка")
    lesson = LessonFactory.create(songs=[song])
    Lesson.objects.filter(pk=lesson.pk).update(updated_at=stale)

    SongAdmin(Song, AdminSite()).delete_model(RequestFactory().post("/"), song)

    lesson.refresh_from_db()
    assert lesson.updated_at > stale


@pytest.mark.django_db
def test_song_admin_delete_queryset_propagates_updated_at_to_related_lessons() -> None:
    stale = datetime(2026, 6, 6, tzinfo=UTC)
    lesson = LessonFactory.create(songs=[SongFactory.create(title="Гроза в степу")])
    Lesson.objects.filter(pk=lesson.pk).update(updated_at=stale)

    SongAdmin(Song, AdminSite()).delete_queryset(
        RequestFactory().post("/"), Song.objects.all()
    )

    lesson.refresh_from_db()
    assert lesson.updated_at > stale
