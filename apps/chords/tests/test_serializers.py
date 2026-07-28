# SPDX-FileCopyrightText: 2025-2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import pytest
from rest_framework.serializers import ValidationError

from apps.chords.api.v1.serializers.chord_detail_serializer import ChordDetailSerializer
from apps.chords.api.v1.serializers.chord_embedded_serializer import (
    ChordEmbeddedSerializer,
)
from apps.chords.api.v1.serializers.chord_position_serializer import (
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
def db_chord_instance(chord_factory: type[FullChordFactory]) -> Chord:
    return chord_factory.create(
        title="C",
        musical_title="C major",
        order_in_note=3,
        start_fret=1,
        has_barre=False,
    )


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
def test_chord_detail_serializer_read(db_chord_instance: Chord) -> None:
    serializer = ChordDetailSerializer(db_chord_instance)
    data = serializer.data

    assert "id" in data
    assert data["title"] == "C"
    assert data["musical_title"] == "C major"
    assert data["order_in_note"] == 3
    assert data["start_fret"] == 1
    assert data["has_barre"] is False
    assert "positions" in data
    assert len(data["positions"]) == 6


@pytest.mark.django_db
def test_chord_embedded_serializer_omits_positions(db_chord_instance: Chord) -> None:
    serializer = ChordEmbeddedSerializer(db_chord_instance)
    data = serializer.data

    assert "positions" not in data
