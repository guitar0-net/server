# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from datetime import UTC, datetime

import pytest
from django.contrib.admin import AdminSite
from django.test import RequestFactory

from apps.lessons.models import Lesson
from apps.lessons.tests.factories import LessonFactory
from apps.schemes.admin import ImageSchemeAdmin
from apps.schemes.models import ImageScheme
from apps.schemes.tests.factories import ImageSchemeFactory
from apps.songs.tests.factories import SongFactory


@pytest.mark.django_db
def test_chord_position_inline_configuration(admin_site: AdminSite) -> None:
    image_scheme_admin = ImageSchemeAdmin(ImageScheme, admin_site)
    assert image_scheme_admin.list_display == ("code", "inscription", "image")
    assert image_scheme_admin.search_fields == ("code", "inscription")


@pytest.mark.django_db
def test_image_scheme_admin_delete_model_propagates_updated_at_to_related_lessons(
    admin_site: AdminSite,
) -> None:
    stale = datetime(2026, 6, 3, tzinfo=UTC)
    scheme = ImageSchemeFactory.create(inscription="Бій «румба»")
    lesson = LessonFactory.create(
        songs=[SongFactory.create(title="Слід на піску", schemes=[scheme])]
    )
    Lesson.objects.filter(pk=lesson.pk).update(updated_at=stale)

    ImageSchemeAdmin(ImageScheme, admin_site).delete_model(
        RequestFactory().post("/"), scheme
    )

    lesson.refresh_from_db()
    assert lesson.updated_at > stale


@pytest.mark.django_db
def test_image_scheme_admin_delete_queryset_propagates_updated_at_to_related_lessons(
    admin_site: AdminSite,
) -> None:
    stale = datetime(2026, 6, 4, tzinfo=UTC)
    scheme = ImageSchemeFactory.create(inscription="Перебір «трійка»")
    lesson = LessonFactory.create(
        songs=[SongFactory.create(title="Дзвони вечірні", schemes=[scheme])]
    )
    Lesson.objects.filter(pk=lesson.pk).update(updated_at=stale)

    ImageSchemeAdmin(ImageScheme, admin_site).delete_queryset(
        RequestFactory().post("/"), ImageScheme.objects.all()
    )

    lesson.refresh_from_db()
    assert lesson.updated_at > stale
