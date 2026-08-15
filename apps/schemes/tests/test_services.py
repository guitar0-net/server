# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for schemes services."""

from collections.abc import Iterable
from datetime import UTC, datetime

import pytest

from apps.lessons.models import Lesson
from apps.lessons.tests.factories import LessonFactory
from apps.schemes import services as scheme_services
from apps.schemes.models import ImageScheme
from apps.schemes.services import ImageSchemeService
from apps.schemes.tests.factories import ImageSchemeFactory
from apps.songs.tests.factories import SongFactory


@pytest.mark.django_db
def test_save_image_scheme_persists_changes_to_the_database() -> None:
    scheme = ImageSchemeFactory.create()
    scheme.inscription = "Бій «вісімка» — оновлено"

    ImageSchemeService.save_image_scheme(scheme=scheme)

    scheme.refresh_from_db()
    assert scheme.inscription == "Бій «вісімка» — оновлено"


@pytest.mark.django_db
def test_save_image_scheme_propagates_updated_at_to_lessons_using_the_scheme() -> None:
    stale = datetime(2026, 4, 1, tzinfo=UTC)
    scheme = ImageSchemeFactory.create(inscription="Перебір «шістка»")
    lesson = LessonFactory.create(
        songs=[SongFactory.create(title="Сонце в долонях", schemes=[scheme])]
    )
    Lesson.objects.filter(pk=lesson.pk).update(updated_at=stale)
    scheme.inscription = "Перебір «шістка» — виправлено"

    ImageSchemeService.save_image_scheme(scheme=scheme)

    lesson.refresh_from_db()
    assert lesson.updated_at > stale


@pytest.mark.django_db
def test_save_image_scheme_leaves_lessons_alone_when_nothing_visible_changed() -> None:
    stale = datetime(2026, 4, 7, tzinfo=UTC)
    scheme = ImageSchemeFactory.create(inscription="Бій «румба»")
    lesson = LessonFactory.create(
        songs=[SongFactory.create(title="黄昏の丘", schemes=[scheme])]
    )
    Lesson.objects.filter(pk=lesson.pk).update(updated_at=stale)

    ImageSchemeService.save_image_scheme(scheme=scheme)

    lesson.refresh_from_db()
    assert lesson.updated_at == stale


@pytest.mark.django_db
def test_save_image_scheme_leaves_lessons_alone_when_only_the_code_changed() -> None:
    stale = datetime(2026, 4, 8, tzinfo=UTC)
    scheme = ImageSchemeFactory.create(inscription="Бій «регтайм»")
    lesson = LessonFactory.create(
        songs=[SongFactory.create(title="Береги дитинства", schemes=[scheme])]
    )
    Lesson.objects.filter(pk=lesson.pk).update(updated_at=stale)
    scheme.code = "ритм-регтайм"

    ImageSchemeService.save_image_scheme(scheme=scheme)

    lesson.refresh_from_db()
    assert lesson.updated_at == stale


@pytest.mark.django_db
def test_save_image_scheme_leaves_lessons_without_that_scheme_alone() -> None:
    stale = datetime(2026, 4, 2, tzinfo=UTC)
    scheme = ImageSchemeFactory.create(inscription="Ритм «галоп»")
    untouched = LessonFactory.create(songs=[SongFactory.create(title="Небо і вітер")])
    Lesson.objects.filter(pk=untouched.pk).update(updated_at=stale)

    ImageSchemeService.save_image_scheme(scheme=scheme)

    untouched.refresh_from_db()
    assert untouched.updated_at == stale


@pytest.mark.django_db
def test_bulk_recalculate_dimensions_propagates_updated_at_to_lessons() -> None:
    stale = datetime(2026, 4, 3, tzinfo=UTC)
    scheme = ImageSchemeFactory.create(inscription="Бій «четвірка»")
    lesson = LessonFactory.create(
        songs=[SongFactory.create(title="Дороги додому", schemes=[scheme])]
    )
    ImageScheme.objects.filter(pk=scheme.pk).update(width=1, height=1)
    Lesson.objects.filter(pk=lesson.pk).update(updated_at=stale)

    ImageSchemeService.bulk_recalculate_dimensions()

    lesson.refresh_from_db()
    assert lesson.updated_at > stale


@pytest.mark.django_db
def test_bulk_recalculate_dimensions_leaves_lessons_alone_when_sizes_match() -> None:
    stale = datetime(2026, 4, 4, tzinfo=UTC)
    scheme = ImageSchemeFactory.create(inscription="Перебір «вісімка»")
    lesson = LessonFactory.create(
        songs=[SongFactory.create(title="Ранок у Карпатах", schemes=[scheme])]
    )
    Lesson.objects.filter(pk=lesson.pk).update(updated_at=stale)

    ImageSchemeService.bulk_recalculate_dimensions()

    lesson.refresh_from_db()
    assert lesson.updated_at == stale


@pytest.mark.django_db
def test_bulk_recalculate_dimensions_discards_the_sizes_when_propagation_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def refuse(scheme_ids: Iterable[int]) -> int:
        raise RuntimeError("зв'язок з уроками недоступний")

    scheme = ImageSchemeFactory.create(inscription="Бій «босанова»")
    ImageScheme.objects.filter(pk=scheme.pk).update(width=3, height=7)
    monkeypatch.setattr(scheme_services, "touch_lessons_for_schemes", refuse)

    with pytest.raises(RuntimeError):
        ImageSchemeService.bulk_recalculate_dimensions()

    # Raw columns, not the instance: reloading an ImageField recomputes the
    # dimensions from the file and would hide what is actually persisted.
    stored = ImageScheme.objects.filter(pk=scheme.pk).values_list("width", "height")
    assert list(stored) == [(3, 7)]


@pytest.mark.django_db
def test_delete_image_scheme_stamps_lessons_before_the_relation_disappears() -> None:
    stale = datetime(2026, 4, 5, tzinfo=UTC)
    scheme = ImageSchemeFactory.create(inscription="Ритм «шафл»")
    lesson = LessonFactory.create(
        songs=[SongFactory.create(title="Пісня для доньки", schemes=[scheme])]
    )
    Lesson.objects.filter(pk=lesson.pk).update(updated_at=stale)

    ImageSchemeService.delete_image_scheme(scheme=scheme)

    lesson.refresh_from_db()
    assert lesson.updated_at > stale


@pytest.mark.django_db
def test_delete_image_schemes_stamps_lessons_before_the_relation_disappears() -> None:
    stale = datetime(2026, 4, 6, tzinfo=UTC)
    schemes = ImageSchemeFactory.create_batch(2)
    lesson = LessonFactory.create(
        songs=[SongFactory.create(title="Тумани над лугом", schemes=schemes)]
    )
    Lesson.objects.filter(pk=lesson.pk).update(updated_at=stale)

    ImageSchemeService.delete_image_schemes(schemes=ImageScheme.objects.all())

    lesson.refresh_from_db()
    assert lesson.updated_at > stale
