# SPDX-FileCopyrightText: 2025 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from apps.chords.constants import MAX_FINGER, MAX_STRING_NUMBER
from apps.chords.models import Chord, ChordPosition
from apps.chords.tests.factories import ChordFactory, ChordPositionFactory


@pytest.mark.django_db
def test_str_without_barre(chord: Chord) -> None:
    chord.has_barre = False
    chord.title = "Am"
    assert str(chord) == "Am"


@pytest.mark.django_db
def test_str_with_barre(chord: Chord) -> None:
    chord.has_barre = True
    chord.title = "Am"
    assert str(chord) == "Am bare"


@pytest.mark.django_db
def test_default_fields() -> None:
    chord = Chord()
    assert chord.order_in_note == 1
    assert chord.start_fret == 1
    assert chord.has_barre is False


@pytest.mark.django_db
def test_string_number_validation(chord: Chord) -> None:
    position = ChordPosition(chord=chord, string_number=0, fret=1, finger=1)

    with pytest.raises(ValidationError):
        position.full_clean()

    position.string_number = MAX_STRING_NUMBER + 1
    with pytest.raises(ValidationError):
        position.full_clean()

    for i in range(1, MAX_STRING_NUMBER + 1):
        pos = ChordPosition(chord=chord, string_number=i, fret=1, finger=1)
        pos.full_clean()


@pytest.mark.django_db
def test_finger_validation(chord: Chord) -> None:
    position = ChordPosition(chord=chord, string_number=1, fret=1, finger=-2)
    with pytest.raises(ValidationError):
        position.full_clean()

    position.finger = MAX_FINGER + 1
    with pytest.raises(ValidationError):
        position.full_clean()

    for f in range(0, MAX_FINGER + 1):
        pos = ChordPosition(chord=chord, string_number=1, fret=1, finger=f)
        pos.full_clean()


@pytest.mark.django_db
def test_unique_constraint(chord: Chord) -> None:
    ChordPositionFactory.create(chord=chord, string_number=1)
    ChordPositionFactory.create(chord=chord, string_number=2)

    with pytest.raises(IntegrityError):
        ChordPositionFactory.create(chord=chord, string_number=1)


@pytest.mark.django_db
def test_unique_constraint_in_different_chords() -> None:
    chord1 = ChordFactory.create()
    chord2 = ChordFactory.create()
    ChordPositionFactory.create(chord=chord1, string_number=1)
    ChordPositionFactory.create(chord=chord2, string_number=1)


@pytest.mark.django_db
def test_ordering(chord: Chord) -> None:
    p3 = ChordPositionFactory.create(chord=chord, string_number=3)
    p1 = ChordPositionFactory.create(chord=chord, string_number=1)
    p5 = ChordPositionFactory.create(chord=chord, string_number=5)

    queryset = list(chord.positions.all())  # pyright: ignore[reportAttributeAccessIssue]
    assert queryset == [p1, p3, p5]


@pytest.mark.django_db
def test_chord_position_str(chord_position: ChordPosition) -> None:
    result = str(chord_position)
    assert f"String #{chord_position.string_number}" in result
    assert f"fret {chord_position.fret}" in result
    assert f"finger {chord_position.finger}" in result
