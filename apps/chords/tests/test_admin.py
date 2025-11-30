# SPDX-FileCopyrightText: 2025 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import pytest
from django.contrib.admin import AdminSite, site
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory
from django.urls import reverse

from apps.accounts.tests.factories.user import UserFactory
from apps.chords.admin import ChordAdmin, ChordPositionInline
from apps.chords.models import Chord, ChordPosition


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
