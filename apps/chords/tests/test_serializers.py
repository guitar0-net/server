# SPDX-FileCopyrightText: 2025 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from typing import Any

import pytest
from rest_framework.serializers import ValidationError

from apps.chords.constants import (
    MAX_FINGER,
    MAX_FRET,
    MAX_STRING_NUMBER,
    MIN_FINGER,
    MIN_FRET,
    MIN_STRING_NUMBER,
)
from apps.chords.models import Chord, ChordPosition
from apps.chords.serializers import ChordPositionSerializer, ChordSerializer


@pytest.fixture
def chord() -> Chord:
    return Chord.objects.create(title="A", musical_title="A Major")


@pytest.fixture
def valid_chord_data() -> dict[str, Any]:
    return {
        "title": "Am",
        "musical_title": "A minor",
        "order_in_note": 2,
        "start_fret": 1,
        "has_barre": False,
        "positions": [
            {"string_number": 1, "fret": 0, "finger": 0},
            {"string_number": 2, "fret": 1, "finger": 1},
            {"string_number": 3, "fret": 2, "finger": 3},
            {"string_number": 4, "fret": 2, "finger": 2},
            {"string_number": 5, "fret": 0, "finger": 0},
            {"string_number": 6, "fret": 0, "finger": 0},
        ],
    }


@pytest.mark.django_db
@pytest.mark.parametrize(
    "data",
    [
        {"string_number": 1, "fret": 0, "finger": 0},
        {"string_number": 2, "fret": -1, "finger": 1},
        {"string_number": 3, "fret": 1, "finger": 4},
    ],
)
def test_chord_position_serializer_valid(data: dict[str, int]) -> None:
    serializer = ChordPositionSerializer(data=data)

    assert serializer.is_valid()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "data, expected_error_key, error_message",
    [
        (
            {"string_number": 0, "fret": 0, "finger": 0},
            "string_number",
            f"Ensure this value is greater than or equal to {MIN_STRING_NUMBER}.",
        ),
        (
            {"string_number": 7, "fret": 0, "finger": 0},
            "string_number",
            f"Ensure this value is less than or equal to {MAX_STRING_NUMBER}.",
        ),
        (
            {"string_number": 1, "fret": -2, "finger": 0},
            "fret",
            f"Ensure this value is greater than or equal to {MIN_FRET}.",
        ),
        (
            {"string_number": 1, "fret": 13, "finger": 0},
            "fret",
            f"Ensure this value is less than or equal to {MAX_FRET}.",
        ),
        (
            {"string_number": 1, "fret": 0, "finger": -2},
            "finger",
            f"Ensure this value is greater than or equal to {MIN_FINGER}.",
        ),
        (
            {"string_number": 1, "fret": 0, "finger": 5},
            "finger",
            f"Ensure this value is less than or equal to {MAX_FINGER}.",
        ),
    ],
)
def test_chord_position_serializer_invalid(
    data: dict[str, int], expected_error_key: str, error_message: str
) -> None:
    serializer = ChordPositionSerializer(data=data)

    with pytest.raises(ValidationError) as exc_info:
        serializer.is_valid(raise_exception=True)
    errors = exc_info.value.detail
    assert expected_error_key in errors, f"Error should be for {expected_error_key}"
    assert str(errors[expected_error_key][0]) == error_message, (  # type: ignore
        "Error message should match custom validator message"
    )


@pytest.mark.django_db
def test_chord_position_serializer_serialization(chord: Chord) -> None:
    position = ChordPosition.objects.create(
        chord=chord, string_number=1, fret=0, finger=0
    )
    serializer = ChordPositionSerializer(position)
    assert serializer.data == {
        "string_number": 1,
        "fret": 0,
        "finger": 0,
    }


@pytest.mark.django_db
def test_create_chord_with_positions(valid_chord_data: dict[str, Any]) -> None:
    serializer = ChordSerializer(data=valid_chord_data)
    assert serializer.is_valid(), serializer.errors
    chord = serializer.save()

    assert chord.title == "Am"
    assert chord.positions.count() == 6
    assert chord.positions.filter(fret=2).count() == 2


@pytest.mark.django_db
def test_create_invalid_position_raises(valid_chord_data: dict[str, Any]) -> None:
    valid_chord_data["positions"][0]["string_number"] = 0

    serializer = ChordSerializer(data=valid_chord_data)
    assert not serializer.is_valid()
    assert "positions" in serializer.errors
    assert "string_number" in serializer.errors["positions"][0]


@pytest.mark.django_db
def test_update_title_only_does_not_delete_positions() -> None:
    chord = Chord.objects.create(title="C", musical_title="C major")
    ChordPosition.objects.create(chord=chord, string_number=1, fret=0, finger=0)

    serializer = ChordSerializer(chord, data={"title": "C major"}, partial=True)
    assert serializer.is_valid(), serializer.errors
    updated = serializer.save()

    assert updated.title == "C major"
    assert updated.positions.count() == 1


@pytest.mark.django_db
def test_update_with_positions_replaces_them() -> None:
    chord = Chord.objects.create(title="Am")
    ChordPosition.objects.create(chord=chord, string_number=1, fret=0, finger=0)

    new_data = {
        "title": "Am7",
        "positions": [
            {"string_number": 1, "fret": 0, "finger": 0},
            {"string_number": 2, "fret": 0, "finger": 0},
        ],
    }

    serializer = ChordSerializer(chord, data=new_data, partial=True)
    assert serializer.is_valid(), serializer.errors
    updated = serializer.save()

    assert updated.positions.count() == 2
    assert updated.positions.filter(fret=0).count() == 2


@pytest.mark.django_db
def test_read_only_positions_on_output() -> None:
    chord = Chord.objects.create(title="G")
    ChordPosition.objects.create(chord=chord, string_number=1, fret=3, finger=2)

    serializer = ChordSerializer(chord)
    data = serializer.data

    assert "positions" in data
    assert len(data["positions"]) == 1
    assert data["positions"][0]["fret"] == 3
