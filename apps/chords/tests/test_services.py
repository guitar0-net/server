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
        {"string_number": 3, "fret": 2, "finger": 3},
        {"string_number": 4, "fret": 2, "finger": 4},
        {"string_number": 5, "fret": 2, "finger": 0},
        {"string_number": 6, "fret": 2, "finger": 0},
    ]

    chord = ChordService.create_chord(positions=positions, chord_fields=chord_fields)

    assert chord.pk is not None
    assert Chord.objects.count() == 1
    assert ChordPosition.objects.count() == 6

    created_positions = list(chord.positions.order_by("string_number"))
    assert created_positions[0].fret == 1
    assert created_positions[1].finger == 2


@pytest.mark.django_db
def test_create_chord_fail_when_not_enough_positions() -> None:
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

    with pytest.raises(ValueError, match="Chord must have exactly 6 positions"):
        ChordService.create_chord(positions=positions, chord_fields=chord_fields)


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
        {"string_number": 1, "fret": 5, "finger": 3},
        {"string_number": 2, "fret": 5, "finger": 3},
        {"string_number": 5, "fret": 5, "finger": 3},
        {"string_number": 6, "fret": 5, "finger": 3},
    ]

    update_data = {
        "title": "Am6",
        "positions": new_positions,
    }

    updated = ChordService.update_chord(chord=chord, data=update_data)

    assert updated.title == "Am6"
    assert ChordPosition.objects.count() == 6

    created_positions = sorted(updated.positions.all(), key=lambda x: x.string_number)
    assert created_positions[0].fret == 5
    assert created_positions[1].finger == 3


@pytest.mark.django_db
def test_update_chord_fail_when_not_enough_positions(
    chord_factory: type[FullChordFactory],
) -> None:
    chord = chord_factory.create()
    positions: list[ChordPositionCreateDict] = [
        {"string_number": 1, "fret": 1, "finger": 1},
        {"string_number": 2, "fret": 2, "finger": 2},
    ]
    update_data = {
        "title": "Am6",
        "positions": positions,
    }

    with pytest.raises(ValueError, match="Chord must have exactly 6 positions"):
        ChordService.update_chord(chord=chord, data=update_data)


@pytest.mark.django_db
def test_delete_chord(chord_factory: type[FullChordFactory]) -> None:
    chord = chord_factory.create()

    ChordService.delete_chord(chord=chord)

    assert Chord.objects.count() == 0
    assert ChordPosition.objects.count() == 0


@pytest.mark.django_db
def test_delete_chord_with_none_pk(chord_factory: type[FullChordFactory]) -> None:
    chord = chord_factory.build()

    ChordService.delete_chord(chord=chord)


@pytest.mark.django_db
def test_replace_positions_creates_positions(chord: Chord) -> None:
    positions_data: list[ChordPositionCreateDict] = [
        {"string_number": 1, "fret": 0, "finger": 0},
        {"string_number": 2, "fret": 1, "finger": 1},
        {"string_number": 3, "fret": 2, "finger": 2},
    ]

    ChordService._replace_positions(chord, positions_data)

    positions = list(chord.positions.all())
    assert len(positions) == 3

    for data, pos in zip(positions_data, positions, strict=True):
        assert pos.string_number == data["string_number"]
        assert pos.fret == data["fret"]
        assert pos.finger == data["finger"]


@pytest.mark.django_db
def test_replace_positions_replaces_existing(chord: Chord) -> None:
    old_positions = [
        ChordPosition.objects.create(chord=chord, string_number=i, fret=i, finger=i)
        for i in range(1, 4)
    ]
    new_positions_data: list[ChordPositionCreateDict] = [
        {"string_number": 1, "fret": 0, "finger": 0},
        {"string_number": 2, "fret": 1, "finger": 1},
    ]

    ChordService._replace_positions(chord, new_positions_data)

    for old in old_positions:
        assert not ChordPosition.objects.filter(pk=old.pk).exists()

    positions = list(chord.positions.all())
    assert len(positions) == len(new_positions_data)
    for data, pos in zip(new_positions_data, positions, strict=True):
        assert pos.string_number == data["string_number"]
        assert pos.fret == data["fret"]
        assert pos.finger == data["finger"]


@pytest.mark.django_db
def test_replace_positions_empty_list(chord: Chord) -> None:
    for i in range(1, 4):
        ChordPosition.objects.create(chord=chord, string_number=i, fret=i, finger=i)

    ChordService._replace_positions(chord, [])

    assert chord.positions.count() == 0
