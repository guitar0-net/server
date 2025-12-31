# SPDX-FileCopyrightText: 2025 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from typing import Any

import pytest
from rest_framework.serializers import ValidationError

from apps.chords.api.serializers import (
    ChordCreateUpdateSerializer,
    ChordOutputSerializer,
    ChordPositionSerializer,
)
from apps.chords.constants import (
    MAX_FINGER,
    MAX_FRET,
    MAX_STRING_NUMBER,
    MIN_FINGER,
    MIN_FRET,
    MIN_STRING_NUMBER,
)
from apps.chords.models import Chord, ChordPosition
from apps.chords.tests.factories import FullChordFactory


@pytest.fixture
def chord() -> Chord:
    return Chord.objects.create(title="A", musical_title="A Major")


@pytest.fixture
def valid_chord_data() -> dict[str, Any]:
    return {
        "title": "Am",
        "musical_title": "A minor",
        "order_in_note": 1,
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


@pytest.fixture
def invalid_duplicate_positions_data() -> dict[str, Any]:
    return {
        "title": "Invalid Chord",
        "musical_title": "Invalid",
        "order_in_note": 1,
        "start_fret": 1,
        "has_barre": False,
        "positions": [
            {"string_number": 1, "fret": 0, "finger": 0},
            {"string_number": 1, "fret": 1, "finger": 1},
            {"string_number": 3, "fret": 2, "finger": 3},
            {"string_number": 4, "fret": 2, "finger": 2},
            {"string_number": 5, "fret": 0, "finger": 0},
            {"string_number": 6, "fret": 0, "finger": 0},
        ],
    }


@pytest.fixture
def invalid_not_enough_positions_data() -> dict[str, Any]:
    return {
        "title": "Invalid Chord",
        "musical_title": "Invalid",
        "order_in_note": 1,
        "start_fret": 1,
        "has_barre": False,
        "positions": [
            {"string_number": 6, "fret": 5, "finger": 1},
            {"string_number": 1, "fret": 7, "finger": 3},
        ],
    }


@pytest.fixture
def db_chord_instance(chord_factory: type[FullChordFactory]) -> Chord:
    return chord_factory.create(
        title="C",
        musical_title="C major",
        order_in_note=3,
        start_fret=1,
        has_barre=False,
    )


# --- ТЕСТЫ СЕРИАЛИЗАТОРА ПОЗИЦИЙ (ChordPositionSerializer) ---


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


# --- ТЕСТЫ СЕРИАЛИЗАТОРА СОЗДАНИЯ/ОБНОВЛЕНИЯ (INPUT) ---


@pytest.mark.django_db
def test_chord_create_serializer_valid(valid_chord_data: dict[str, Any]) -> None:
    serializer = ChordCreateUpdateSerializer(data=valid_chord_data)
    assert serializer.is_valid() is True
    assert "positions" in serializer.validated_data
    assert len(serializer.validated_data["positions"]) == 6


@pytest.mark.django_db
def test_chord_create_serializer_invalid_duplicate_positions(
    invalid_duplicate_positions_data: dict[str, Any],
) -> None:
    serializer = ChordCreateUpdateSerializer(data=invalid_duplicate_positions_data)
    assert serializer.is_valid() is False
    assert "positions" in serializer.errors
    assert (
        "Duplicate string numbers are not allowed." in serializer.errors["positions"][0]
    )


@pytest.mark.django_db
def test_chord_create_serializer_invalid_not_enough_positions(
    invalid_not_enough_positions_data: dict[str, Any],
) -> None:
    serializer = ChordCreateUpdateSerializer(data=invalid_not_enough_positions_data)
    assert serializer.is_valid() is False
    assert "positions" in serializer.errors
    assert "Chord must has only 6 positions." in serializer.errors["positions"][0]


@pytest.mark.django_db
def test_chord_create_serializer_missing_required_field(
    valid_chord_data: dict[str, Any],
) -> None:
    invalid_data = valid_chord_data.copy()
    invalid_data.pop("title")
    serializer = ChordCreateUpdateSerializer(data=invalid_data)
    assert serializer.is_valid() is False
    assert "title" in serializer.errors


# --- ТЕСТЫ СЕРИАЛИЗАТОРА ВЫВОДА (OUTPUT) ---


@pytest.mark.django_db
def test_chord_output_serializer_read(db_chord_instance: Chord) -> None:
    serializer = ChordOutputSerializer(db_chord_instance)
    data = serializer.data

    assert "id" in data
    assert data["title"] == "C"
    assert data["musical_title"] == "C major"
    assert data["order_in_note"] == 3
    assert data["start_fret"] == 1
    assert data["has_barre"] is False
    assert "positions" in data
    assert len(data["positions"]) == 6
