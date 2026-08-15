# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for sync API views."""

from datetime import UTC, datetime, timedelta

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.chords.services import ChordService
from apps.chords.tests.factories import ChordFactory, FullChordFactory
from apps.courses.tests.factories import CourseFactory, CourseLessonFactory
from apps.lessons.models import Lesson
from apps.lessons.tests.factories import LessonFactory
from apps.schemes.services import ImageSchemeService
from apps.schemes.tests.factories import ImageSchemeFactory
from apps.songs.tests.factories import SongFactory

# =============================================================================
# LessonsSyncView — GET /api/v1/sync/lessons/ — top-level keys
# =============================================================================


@pytest.mark.django_db
def test_sync_lessons_returns_200(api_client: APIClient) -> None:
    response = api_client.get(reverse("sync-lessons"))

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_sync_lessons_response_contains_version_key(api_client: APIClient) -> None:
    LessonFactory.create(is_published=True)

    response = api_client.get(reverse("sync-lessons"))

    assert "version" in response.data


@pytest.mark.django_db
def test_sync_lessons_response_contains_lesson_uuids_key(api_client: APIClient) -> None:
    response = api_client.get(reverse("sync-lessons"))

    assert "lesson_uuids" in response.data


@pytest.mark.django_db
def test_sync_lessons_response_contains_lessons_key(api_client: APIClient) -> None:
    response = api_client.get(reverse("sync-lessons"))

    assert "lessons" in response.data


@pytest.mark.django_db
def test_sync_lessons_response_contains_songs_key(api_client: APIClient) -> None:
    response = api_client.get(reverse("sync-lessons"))

    assert "songs" in response.data


@pytest.mark.django_db
def test_sync_lessons_response_contains_chords_key(api_client: APIClient) -> None:
    response = api_client.get(reverse("sync-lessons"))

    assert "chords" in response.data


@pytest.mark.django_db
def test_sync_lessons_response_contains_schemes_key(api_client: APIClient) -> None:
    response = api_client.get(reverse("sync-lessons"))

    assert "schemes" in response.data


@pytest.mark.django_db
def test_sync_lessons_response_contains_course_uuids_key(api_client: APIClient) -> None:
    response = api_client.get(reverse("sync-lessons"))

    assert "course_uuids" in response.data


@pytest.mark.django_db
def test_sync_lessons_response_contains_courses_key(api_client: APIClient) -> None:
    response = api_client.get(reverse("sync-lessons"))

    assert "courses" in response.data


@pytest.mark.django_db
def test_sync_lessons_response_contains_course_lessons_key(
    api_client: APIClient,
) -> None:
    response = api_client.get(reverse("sync-lessons"))

    assert "course_lessons" in response.data


# =============================================================================
# Lessons
# =============================================================================


@pytest.mark.django_db
def test_sync_lessons_includes_published_lesson(api_client: APIClient) -> None:
    lesson = LessonFactory.create(is_published=True, title="Кавер на Кино")

    response = api_client.get(reverse("sync-lessons"))

    uuids = [item["uuid"] for item in response.data["lessons"]]
    assert str(lesson.uuid) in uuids


@pytest.mark.django_db
def test_sync_lessons_excludes_unpublished_lesson(api_client: APIClient) -> None:
    LessonFactory.create(is_published=False, title="Черновик")

    response = api_client.get(reverse("sync-lessons"))

    assert response.data["lessons"] == []


@pytest.mark.django_db
def test_sync_lessons_lesson_uuids_excludes_unpublished(api_client: APIClient) -> None:
    secret = LessonFactory.create(is_published=False)

    response = api_client.get(reverse("sync-lessons"))

    assert str(secret.uuid) not in response.data["lesson_uuids"]


@pytest.mark.django_db
def test_sync_lessons_lesson_contains_updated_at_field(api_client: APIClient) -> None:
    LessonFactory.create(is_published=True)

    response = api_client.get(reverse("sync-lessons"))

    assert "updated_at" in response.data["lessons"][0]


@pytest.mark.django_db
def test_sync_lessons_lesson_uuids_contains_all_published(
    api_client: APIClient,
) -> None:
    lesson_a = LessonFactory.create(is_published=True)
    lesson_b = LessonFactory.create(is_published=True)

    response = api_client.get(reverse("sync-lessons"))

    assert str(lesson_a.uuid) in response.data["lesson_uuids"]
    assert str(lesson_b.uuid) in response.data["lesson_uuids"]


# =============================================================================
# Songs — flat top-level array
# =============================================================================


@pytest.mark.django_db
def test_sync_lessons_songs_are_in_top_level_array(api_client: APIClient) -> None:
    song = SongFactory.create(title="Звезда по имени Солнце")
    LessonFactory.create(is_published=True, songs=[song])

    response = api_client.get(reverse("sync-lessons"))

    titles = [s["title"] for s in response.data["songs"]]
    assert "Звезда по имени Солнце" in titles


@pytest.mark.django_db
def test_sync_lessons_song_has_lesson_uuid(api_client: APIClient) -> None:
    song = SongFactory.create()
    lesson = LessonFactory.create(is_published=True, songs=[song])

    response = api_client.get(reverse("sync-lessons"))

    song_data = next(s for s in response.data["songs"] if s["uuid"] == str(song.uuid))
    assert song_data["lesson_uuid"] == str(lesson.uuid)


@pytest.mark.django_db
def test_sync_lessons_song_has_chord_ids(api_client: APIClient) -> None:
    chord = ChordFactory.create()
    song = SongFactory.create(chords=[chord])
    LessonFactory.create(is_published=True, songs=[song])

    response = api_client.get(reverse("sync-lessons"))

    song_data = next(s for s in response.data["songs"] if s["uuid"] == str(song.uuid))
    assert chord.id in song_data["chord_ids"]


@pytest.mark.django_db
def test_sync_lessons_song_has_scheme_ids(api_client: APIClient) -> None:
    scheme = ImageSchemeFactory.create()
    song = SongFactory.create(schemes=[scheme])
    LessonFactory.create(is_published=True, songs=[song])

    response = api_client.get(reverse("sync-lessons"))

    song_data = next(s for s in response.data["songs"] if s["uuid"] == str(song.uuid))
    assert scheme.id in song_data["scheme_ids"]


@pytest.mark.django_db
def test_sync_lessons_songs_from_unpublished_lesson_excluded(
    api_client: APIClient,
) -> None:
    song = SongFactory.create()
    LessonFactory.create(is_published=False, songs=[song])

    response = api_client.get(reverse("sync-lessons"))

    assert response.data["songs"] == []


# =============================================================================
# Chords — flat, deduplicated
# =============================================================================


@pytest.mark.django_db
def test_sync_lessons_chords_are_in_top_level_array(api_client: APIClient) -> None:
    chord = ChordFactory.create(title="Am")
    song = SongFactory.create(chords=[chord])
    LessonFactory.create(is_published=True, songs=[song])

    response = api_client.get(reverse("sync-lessons"))

    chord_ids = [c["id"] for c in response.data["chords"]]
    assert chord.id in chord_ids


@pytest.mark.django_db
def test_sync_lessons_chord_shared_across_songs_appears_once(
    api_client: APIClient,
) -> None:
    chord = ChordFactory.create(title="Am")
    song1 = SongFactory.create(chords=[chord])
    song2 = SongFactory.create(chords=[chord])
    LessonFactory.create(is_published=True, songs=[song1, song2])

    response = api_client.get(reverse("sync-lessons"))

    chord_ids = [c["id"] for c in response.data["chords"]]
    assert chord_ids.count(chord.id) == 1


# =============================================================================
# Delta sync via ?since=
# =============================================================================


@pytest.mark.django_db
def test_sync_lessons_since_filters_older_lessons(api_client: APIClient) -> None:
    cutoff = datetime(2026, 3, 1, tzinfo=UTC)
    old = LessonFactory.create(is_published=True)
    Lesson.objects.filter(pk=old.pk).update(updated_at=cutoff - timedelta(days=5))

    response = api_client.get(reverse("sync-lessons"), {"since": cutoff.isoformat()})

    assert response.data["lessons"] == []


@pytest.mark.django_db
def test_sync_lessons_since_includes_newer_lessons(api_client: APIClient) -> None:
    cutoff = datetime(2026, 3, 1, tzinfo=UTC)
    newer = LessonFactory.create(is_published=True, title="Новый урок")
    Lesson.objects.filter(pk=newer.pk).update(updated_at=cutoff + timedelta(days=1))

    response = api_client.get(reverse("sync-lessons"), {"since": cutoff.isoformat()})

    uuids = [item["uuid"] for item in response.data["lessons"]]
    assert str(newer.uuid) in uuids


@pytest.mark.django_db
def test_sync_lessons_since_lesson_uuids_always_contains_all_published(
    api_client: APIClient,
) -> None:
    cutoff = datetime(2026, 3, 1, tzinfo=UTC)
    old = LessonFactory.create(is_published=True)
    Lesson.objects.filter(pk=old.pk).update(updated_at=cutoff - timedelta(days=5))

    response = api_client.get(reverse("sync-lessons"), {"since": cutoff.isoformat()})

    assert response.data["lessons"] == []
    assert str(old.uuid) in response.data["lesson_uuids"]


@pytest.mark.django_db
def test_sync_lessons_delta_songs_scoped_to_changed_lessons(
    api_client: APIClient,
) -> None:
    cutoff = datetime(2026, 3, 1, tzinfo=UTC)

    old_song = SongFactory.create(title="Старая песня")
    old_lesson = LessonFactory.create(is_published=True, songs=[old_song])
    Lesson.objects.filter(pk=old_lesson.pk).update(
        updated_at=cutoff - timedelta(days=5)
    )

    new_song = SongFactory.create(title="Новая песня")
    new_lesson = LessonFactory.create(is_published=True, songs=[new_song])
    Lesson.objects.filter(pk=new_lesson.pk).update(
        updated_at=cutoff + timedelta(days=1)
    )

    response = api_client.get(reverse("sync-lessons"), {"since": cutoff.isoformat()})

    song_titles = [s["title"] for s in response.data["songs"]]
    assert "Новая песня" in song_titles
    assert "Старая песня" not in song_titles


@pytest.mark.django_db
def test_sync_lessons_delta_chords_scoped_to_changed_lessons(
    api_client: APIClient,
) -> None:
    cutoff = datetime(2026, 3, 1, tzinfo=UTC)

    old_chord = ChordFactory.create(title="Am")
    old_song = SongFactory.create(chords=[old_chord])
    old_lesson = LessonFactory.create(is_published=True, songs=[old_song])
    Lesson.objects.filter(pk=old_lesson.pk).update(
        updated_at=cutoff - timedelta(days=5)
    )

    new_chord = ChordFactory.create(title="Em")
    new_song = SongFactory.create(chords=[new_chord])
    new_lesson = LessonFactory.create(is_published=True, songs=[new_song])
    Lesson.objects.filter(pk=new_lesson.pk).update(
        updated_at=cutoff + timedelta(days=1)
    )

    response = api_client.get(reverse("sync-lessons"), {"since": cutoff.isoformat()})

    chord_ids = [c["id"] for c in response.data["chords"]]
    assert new_chord.id in chord_ids
    assert old_chord.id not in chord_ids


@pytest.mark.django_db
def test_sync_lessons_invalid_since_returns_400(api_client: APIClient) -> None:
    response = api_client.get(reverse("sync-lessons"), {"since": "not-a-date"})

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_sync_lessons_naive_since_is_treated_as_utc(api_client: APIClient) -> None:
    cutoff = datetime(2026, 4, 1, tzinfo=UTC)
    newer = LessonFactory.create(is_published=True)
    Lesson.objects.filter(pk=newer.pk).update(updated_at=cutoff + timedelta(hours=1))
    naive_iso = cutoff.replace(tzinfo=None).isoformat()

    response = api_client.get(reverse("sync-lessons"), {"since": naive_iso})

    uuids = [item["uuid"] for item in response.data["lessons"]]
    assert str(newer.uuid) in uuids


# =============================================================================
# ContentVersionView — GET /api/v1/sync/version/
# =============================================================================


@pytest.mark.django_db
def test_sync_version_returns_200(api_client: APIClient) -> None:
    response = api_client.get(reverse("sync-version"))

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_sync_version_returns_version_key(api_client: APIClient) -> None:
    LessonFactory.create(is_published=True)

    response = api_client.get(reverse("sync-version"))

    assert "version" in response.data


@pytest.mark.django_db
def test_sync_version_returns_none_when_no_published_lessons(
    api_client: APIClient,
) -> None:
    response = api_client.get(reverse("sync-version"))

    assert response.data["version"] is None


@pytest.mark.django_db
def test_sync_version_value_is_valid_iso8601(api_client: APIClient) -> None:
    LessonFactory.create(is_published=True)

    response = api_client.get(reverse("sync-version"))

    datetime.fromisoformat(response.data["version"])


# =============================================================================
# Courses
# =============================================================================


@pytest.mark.django_db
def test_sync_lessons_courses_includes_published_course(api_client: APIClient) -> None:
    course = CourseFactory.create(is_published=True, title="Уроки для начинающих")

    response = api_client.get(reverse("sync-lessons"))

    uuids = [c["uuid"] for c in response.data["courses"]]
    assert str(course.uuid) in uuids


@pytest.mark.django_db
def test_sync_lessons_courses_excludes_unpublished_course(
    api_client: APIClient,
) -> None:
    CourseFactory.create(is_published=False)

    response = api_client.get(reverse("sync-lessons"))

    assert response.data["courses"] == []


@pytest.mark.django_db
def test_sync_lessons_course_uuids_contains_published(api_client: APIClient) -> None:
    course = CourseFactory.create(is_published=True)

    response = api_client.get(reverse("sync-lessons"))

    assert str(course.uuid) in response.data["course_uuids"]


@pytest.mark.django_db
def test_sync_lessons_course_uuids_excludes_unpublished(api_client: APIClient) -> None:
    secret = CourseFactory.create(is_published=False)

    response = api_client.get(reverse("sync-lessons"))

    assert str(secret.uuid) not in response.data["course_uuids"]


# =============================================================================
# Course lessons — flat top-level array
# =============================================================================


@pytest.mark.django_db
def test_sync_lessons_course_lessons_contain_membership(api_client: APIClient) -> None:
    lesson = LessonFactory.create(is_published=True)
    course = CourseFactory.create(is_published=True)
    CourseLessonFactory.create(course=course, lesson=lesson, order=1)

    response = api_client.get(reverse("sync-lessons"))

    found = next(
        (
            cl
            for cl in response.data["course_lessons"]
            if cl["course_uuid"] == str(course.uuid)
            and cl["lesson_uuid"] == str(lesson.uuid)
        ),
        None,
    )
    assert found is not None


@pytest.mark.django_db
def test_sync_lessons_course_lessons_have_order(api_client: APIClient) -> None:
    lesson = LessonFactory.create(is_published=True)
    course = CourseFactory.create(is_published=True)
    CourseLessonFactory.create(course=course, lesson=lesson, order=3)

    response = api_client.get(reverse("sync-lessons"))

    found = next(
        cl
        for cl in response.data["course_lessons"]
        if cl["course_uuid"] == str(course.uuid)
    )
    assert found["order"] == 3


@pytest.mark.django_db
def test_sync_lessons_course_lessons_exclude_unpublished_lesson(
    api_client: APIClient,
) -> None:
    published = LessonFactory.create(is_published=True)
    unpublished = LessonFactory.create(is_published=False)
    course = CourseFactory.create(is_published=True)
    CourseLessonFactory.create(course=course, lesson=published, order=1)
    CourseLessonFactory.create(course=course, lesson=unpublished, order=2)

    response = api_client.get(reverse("sync-lessons"))

    lesson_uuids_in_cl = [cl["lesson_uuid"] for cl in response.data["course_lessons"]]
    assert str(published.uuid) in lesson_uuids_in_cl
    assert str(unpublished.uuid) not in lesson_uuids_in_cl


# =============================================================================
# Delta sync must surface changes that originate below the lesson
# =============================================================================


@pytest.mark.django_db
def test_delta_sync_returns_a_chord_whose_svg_was_regenerated(
    api_client: APIClient,
) -> None:
    stale = datetime(2026, 5, 1, tzinfo=UTC)
    chord = FullChordFactory.create(title="Dmaj7")
    lesson = LessonFactory.create(
        is_published=True,
        songs=[SongFactory.create(title="Вечір над рікою", chords=[chord])],
    )
    Lesson.objects.filter(pk=lesson.pk).update(updated_at=stale)

    ChordService.bulk_regenerate_svgs()
    response = api_client.get(reverse("sync-lessons"), {"since": stale.isoformat()})

    assert [entry["id"] for entry in response.data["chords"]] == [chord.pk]


@pytest.mark.django_db
def test_delta_sync_returns_a_scheme_whose_inscription_was_edited(
    api_client: APIClient,
) -> None:
    stale = datetime(2026, 5, 2, tzinfo=UTC)
    scheme = ImageSchemeFactory.create(inscription="Бій «вальс»")
    lesson = LessonFactory.create(
        is_published=True,
        songs=[SongFactory.create(title="Стежка в гори", schemes=[scheme])],
    )
    Lesson.objects.filter(pk=lesson.pk).update(updated_at=stale)
    scheme.inscription = "Бій «вальс» — уточнено"

    ImageSchemeService.save_image_scheme(scheme=scheme)
    response = api_client.get(reverse("sync-lessons"), {"since": stale.isoformat()})

    assert [entry["id"] for entry in response.data["schemes"]] == [scheme.pk]
