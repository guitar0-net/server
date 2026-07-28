# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Selectors for the lessons app."""

import uuid as uuid_module

from django.db.models import Prefetch, QuerySet

from apps.courses.models import Course
from apps.lessons.models import Lesson


def get_published_lessons() -> QuerySet[Lesson]:
    """Return a QuerySet of all published lessons."""
    return (
        Lesson.objects
        .filter(is_published=True)
        .order_by("id")
        .prefetch_related("songs")
    )


def get_course_for_lesson(lesson: Lesson, course_uuid: str) -> Course | None:
    """Return a published Course the given lesson belongs to, or None."""
    try:
        parsed = uuid_module.UUID(course_uuid)
    except ValueError:
        return None
    return Course.objects.filter(lessons=lesson, uuid=parsed, is_published=True).first()


def get_lesson_by_uuid(uuid: str) -> Lesson | None:
    """Return a published Lesson by UUID with related data, or None."""
    return (
        Lesson.objects
        .filter(uuid=uuid, is_published=True)
        .prefetch_related(
            "songs__chords",
            "songs__schemes",
            Prefetch(
                "addition_lessons",
                queryset=Lesson.objects.filter(is_published=True).prefetch_related(
                    "songs"
                ),
            ),
        )
        .first()
    )
