# SPDX-FileCopyrightText: 2025 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import pytest

from apps.chords.models import Chord, ChordPosition
from apps.chords.services import ChordCreateDict, ChordPositionCreateDict, ChordService
from apps.chords.tests.factories import FullChordFactory


@pytest.mark.django_db
def test_create_chord_success() -> None:
    chord_fields: ChordCreateDict = {
        "title": "Am",
        "musical_title": "A minor",
        "order_in_note": 1,
        "start_fret": 1,
        "has_barre": False,
    }

    positions: list[ChordPositionCreateDict] = [
        {"string_number": 1, "fret": 1, "finger": 1},
        {"string_number": 2, "fret": 2, "finger": 2},
    ]

    chord = ChordService.create_chord(positions=positions, chord_fields=chord_fields)

    assert chord.pk is not None
    assert Chord.objects.count() == 1
    assert ChordPosition.objects.count() == 2

    created_positions = list(chord.positions.order_by("string_number"))
    assert created_positions[0].fret == 1
    assert created_positions[1].finger == 2


@pytest.mark.django_db
def test_update_chord_without_positions(chord_factory: type[FullChordFactory]) -> None:
    chord = chord_factory.create(
        title="Am",
        musical_title="A minor",
        order_in_note=1,
        start_fret=1,
        has_barre=False,
    )

    update_data = {
        "title": "Am7",
        "start_fret": 2,
    }

    updated = ChordService.update_chord(chord=chord, data=update_data)

    assert updated.title == "Am7"
    assert updated.start_fret == 2
    assert ChordPosition.objects.count() == 6


@pytest.mark.django_db
def test_update_chord_with_positions_replaces_old(
    chord_factory: type[FullChordFactory],
) -> None:
    chord = chord_factory.create(
        title="Am",
        musical_title="A minor",
        order_in_note=1,
        start_fret=1,
        has_barre=False,
    )

    new_positions = [
        {"string_number": 3, "fret": 4, "finger": 2},
        {"string_number": 4, "fret": 5, "finger": 3},
    ]

    update_data = {
        "title": "Am6",
        "positions": new_positions,
    }

    updated = ChordService.update_chord(chord=chord, data=update_data)

    assert updated.title == "Am6"
    assert ChordPosition.objects.count() == 2

    created_positions = sorted(updated.positions.all(), key=lambda x: x.string_number)
    assert created_positions[0].fret == 4
    assert created_positions[1].finger == 3


@pytest.mark.django_db
def test_delete_chord() -> None:
    chord = Chord.objects.create(
        title="Am",
        musical_title="A minor",
        order_in_note=1,
        start_fret=1,
        has_barre=False,
    )

    ChordPosition.objects.create(chord=chord, string_number=1, fret=1, finger=1)

    ChordService.delete_chord(chord=chord)

    assert Chord.objects.count() == 0
    assert ChordPosition.objects.count() == 0
