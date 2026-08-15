# SPDX-FileCopyrightText: 2025 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from datetime import UTC, datetime

import pytest
from django.contrib.admin import AdminSite, site
from django.core.exceptions import PermissionDenied
from django.forms import ModelForm, modelform_factory
from django.http import HttpResponse
from django.test import RequestFactory
from django.urls import reverse

from apps.accounts.tests.factories.user import UserFactory
from apps.chords.admin import ChordAdmin, ChordPositionInline
from apps.chords.models import Chord, ChordPosition
from apps.chords.tests.factories import FullChordFactory
from apps.lessons.models import Lesson
from apps.lessons.tests.factories import LessonFactory
from apps.songs.tests.factories import SongFactory


@pytest.fixture
def admin_site() -> AdminSite:
    return site


@pytest.fixture
def chord_admin(admin_site: AdminSite) -> ChordAdmin:
    return ChordAdmin(Chord, admin_site)


@pytest.mark.django_db
def test_chord_position_inline_configuration(admin_site: AdminSite) -> None:
    inline = ChordPositionInline(Chord, admin_site)
    assert inline.model == ChordPosition
    assert inline.extra == 0
    assert inline.fields == ("string_number", "fret", "finger")


def test_chord_admin_configuration(chord_admin: ChordAdmin) -> None:
    """Tests the configuration attributes of ChordAdmin.

    Verifies list_display, list_filter, search_fields, ordering, and inlines.
    """
    assert chord_admin.list_display == (
        "title",
        "musical_title",
        "start_fret",
        "has_barre",
    )
    assert chord_admin.list_filter == ("has_barre",)
    assert chord_admin.search_fields == ("title", "musical_title")
    assert chord_admin.ordering == ("order_in_note",)
    assert chord_admin.inlines == [ChordPositionInline]


@pytest.mark.django_db
def test_chord_admin_inline_in_list_view_success(
    chord_admin: ChordAdmin,
) -> None:
    factory = RequestFactory()
    superuser = UserFactory.create(is_superuser=True)
    request = factory.get(reverse("admin:chords_chord_changelist"))
    request.user = superuser
    response = chord_admin.changelist_view(request)
    assert response.status_code == HttpResponse.status_code


@pytest.mark.django_db
def test_chord_admin_inline_in_list_view_fail(
    chord_admin: ChordAdmin,
) -> None:
    factory = RequestFactory()
    user = UserFactory.create(is_superuser=False)
    request = factory.get(reverse("admin:chords_chord_changelist"))
    request.user = user
    with pytest.raises(PermissionDenied):
        chord_admin.changelist_view(request)


def _make_bound_chord_form(chord: Chord) -> ModelForm:  # type: ignore[type-arg]
    """Return a bound, validated ModelForm for chord with save_m2m attached."""
    ChordFormClass = modelform_factory(Chord, fields="__all__")  # noqa: N806
    data = {
        "title": chord.title,
        "musical_title": chord.musical_title,
        "order_in_note": chord.order_in_note,
        "start_fret": chord.start_fret,
        "has_barre": chord.has_barre,
        "svg_horizontal": chord.svg_horizontal,
        "svg_vertical": chord.svg_vertical,
    }
    form = ChordFormClass(data=data, instance=chord)
    form.is_valid()
    form.save(commit=False)
    return form


@pytest.mark.django_db
@pytest.mark.parametrize("change", [True, False])
def test_chord_admin_save_related_populates_svg(
    chord_admin: ChordAdmin,
    change: bool,
) -> None:
    chord = FullChordFactory.create()
    form = _make_bound_chord_form(chord)
    request = RequestFactory().post("/")
    request.user = UserFactory.create(is_superuser=True)
    chord_admin.save_related(request, form, [], change=change)
    chord.refresh_from_db()
    assert chord.svg_horizontal
    assert chord.svg_vertical


@pytest.mark.django_db
def test_chord_admin_save_persists_a_field_edited_in_the_form(
    chord_admin: ChordAdmin,
) -> None:
    chord = FullChordFactory.create(musical_title="Ре-мажор")
    request = RequestFactory().post("/")
    request.user = UserFactory.create(is_superuser=True)
    chord.musical_title = "Ре-мажор сьомий"
    form = _make_bound_chord_form(chord)

    chord_admin.save_model(request, chord, form, change=True)
    chord_admin.save_related(request, form, [], change=True)

    chord.refresh_from_db()
    assert chord.musical_title == "Ре-мажор сьомий"


@pytest.mark.django_db
def test_chord_admin_save_leaves_lessons_alone_when_nothing_was_edited(
    chord_admin: ChordAdmin,
) -> None:
    stale = datetime(2026, 6, 3, tzinfo=UTC)
    chord = FullChordFactory.create(title="Cmin7")
    lesson = LessonFactory.create(
        songs=[SongFactory.create(title="Дощ у неділю", chords=[chord])]
    )
    request = RequestFactory().post("/")
    request.user = UserFactory.create(is_superuser=True)
    chord_admin.save_related(request, _make_bound_chord_form(chord), [], change=True)
    Lesson.objects.filter(pk=lesson.pk).update(updated_at=stale)

    chord_admin.save_related(request, _make_bound_chord_form(chord), [], change=True)

    lesson.refresh_from_db()
    assert lesson.updated_at == stale


@pytest.mark.django_db
def test_chord_admin_delete_model_propagates_updated_at_to_related_lessons(
    chord_admin: ChordAdmin,
) -> None:
    stale = datetime(2026, 6, 1, tzinfo=UTC)
    chord = FullChordFactory.create(title="Cmaj9")
    lesson = LessonFactory.create(
        songs=[SongFactory.create(title="Мелодія осені", chords=[chord])]
    )
    Lesson.objects.filter(pk=lesson.pk).update(updated_at=stale)

    chord_admin.delete_model(RequestFactory().post("/"), chord)

    lesson.refresh_from_db()
    assert lesson.updated_at > stale


@pytest.mark.django_db
def test_chord_admin_delete_queryset_propagates_updated_at_to_related_lessons(
    chord_admin: ChordAdmin,
) -> None:
    stale = datetime(2026, 6, 2, tzinfo=UTC)
    chord = FullChordFactory.create(title="Emadd9")
    lesson = LessonFactory.create(
        songs=[SongFactory.create(title="Хмари над містом", chords=[chord])]
    )
    Lesson.objects.filter(pk=lesson.pk).update(updated_at=stale)

    chord_admin.delete_queryset(RequestFactory().post("/"), Chord.objects.all())

    lesson.refresh_from_db()
    assert lesson.updated_at > stale
