# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for lessons selectors."""

import pytest
from pytest_django.fixtures import DjangoAssertNumQueries

from apps.courses.tests.factories import CourseFactory
from apps.lessons.selectors import (
    get_course_for_lesson,
    get_lesson_by_uuid,
    get_published_lessons,
)
from apps.lessons.tests.factories import LessonFactory


@pytest.mark.django_db
def test_get_published_lessons_excludes_unpublished() -> None:
    LessonFactory.create(title="Published", is_published=True)
    LessonFactory.create(title="Unpublished", is_published=False)

    lessons = get_published_lessons()

    assert lessons.count() == 1
    lesson = lessons.first()
    assert lesson
    assert lesson.title == "Published"


@pytest.mark.django_db
def test_get_lesson_by_uuid() -> None:
    lesson = LessonFactory.create(title="Test Lesson")

    result = get_lesson_by_uuid(str(lesson.uuid))

    assert result is not None
    assert result.title == "Test Lesson"


@pytest.mark.django_db
def test_get_lesson_by_uuid_returns_none_for_unpublished() -> None:
    lesson = LessonFactory.create(is_published=False)

    result = get_lesson_by_uuid(str(lesson.uuid))

    assert result is None


@pytest.mark.django_db
def test_get_course_for_lesson_returns_course_when_lesson_belongs_to_it() -> None:
    lesson = LessonFactory.create()
    course = CourseFactory.create(lessons=[lesson])

    result = get_course_for_lesson(lesson, str(course.uuid))

    assert result == course


@pytest.mark.django_db
def test_get_course_for_lesson_returns_none_on_malformed_uuid() -> None:
    lesson = LessonFactory.create()

    result = get_course_for_lesson(lesson, "не-uuid-строка")

    assert result is None


@pytest.mark.django_db
def test_get_course_for_lesson_returns_none_when_course_is_unpublished() -> None:
    lesson = LessonFactory.create()
    course = CourseFactory.create(lessons=[lesson], is_published=False)

    result = get_course_for_lesson(lesson, str(course.uuid))

    assert result is None


@pytest.mark.django_db
def test_get_course_for_lesson_returns_none_when_lesson_not_in_course() -> None:
    lesson = LessonFactory.create()
    other_course = CourseFactory.create()

    result = get_course_for_lesson(lesson, str(other_course.uuid))

    assert result is None


@pytest.mark.django_db
def test_get_lesson_by_uuid_filters_unpublished_addition_lessons() -> None:
    published = LessonFactory.create(title="Published", is_published=True)
    unpublished = LessonFactory.create(title="Unpublished", is_published=False)
    lesson = LessonFactory.create(addition_lessons=[published, unpublished])

    result = get_lesson_by_uuid(str(lesson.uuid))

    assert result is not None
    addition_titles = [lesson.title for lesson in result.addition_lessons.all()]
    assert addition_titles == ["Published"]


@pytest.mark.django_db
def test_get_lesson_by_uuid_prefetches_songs_of_addition_lessons(
    django_assert_num_queries: DjangoAssertNumQueries,
) -> None:
    additions = LessonFactory.create_batch(3, songs=2)
    lesson = LessonFactory.create(addition_lessons=additions)

    with django_assert_num_queries(4):
        result = get_lesson_by_uuid(str(lesson.uuid))
        assert result is not None
        for addition in result.addition_lessons.all():
            list(addition.songs.all())
