# SPDX-FileCopyrightText: 2025 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Services for the chords app."""

from typing import Any, TypedDict

from django.db import transaction

from .models import Chord, ChordPosition


class ChordPositionCreateDict(TypedDict):
    """Describe fields for a chord positions when creating."""

    string_number: int
    fret: int
    finger: int


class ChordCreateDict(TypedDict):
    """Describe fields for a chord creating."""

    title: str
    musical_title: str
    order_in_note: int
    start_fret: int
    has_barre: bool


class ChordUpdateDict(TypedDict, total=False):
    """Describe fields for a chord updating."""

    title: str
    musical_title: str
    order_in_note: int
    start_fret: int
    has_barre: bool
    positions: list[ChordPositionCreateDict]


class ChordService:
    """Contains business logic execution and data manipulation for the Chord entity."""

    @staticmethod
    @transaction.atomic
    def create_chord(
        *,
        positions: list[ChordPositionCreateDict],
        chord_fields: ChordCreateDict,
    ) -> Chord:
        """Create a new Chord instance and its related ChordPositions atomically.

        Args:
            positions (list[dict]): List of dictionaries describing string positions.
            chord_fields: Dict for Chord model (ChordCreateDict)

        Returns:
            Chord: The created Chord instance.
        """
        chord = Chord.objects.create(**chord_fields)
        ChordService._replace_positions(chord, positions)
        return chord

    @staticmethod
    @transaction.atomic
    def update_chord(
        *,
        chord: Chord,
        data: dict[str, Any],
    ) -> Chord:
        """Update an existing Chord and handles full replacement of nested positions.

        Args:
            chord (Chord): The existing Chord instance to update.
            data (dict): Dictionary containing fields to update.

        Returns:
            Chord: The updated Chord instance.
        """
        positions_data = data.pop("positions", None)
        for field, value in data.items():
            setattr(chord, field, value)
        chord.save()

        if positions_data is not None:
            ChordService._replace_positions(chord, positions_data)

        return chord

    @staticmethod
    def delete_chord(*, chord: Chord) -> None:
        """Delete a Chord instance.

        Args:
            chord (Chord): The Chord instance to delete.
        """
        if chord.pk is not None:
            chord.delete()

    @staticmethod
    def _replace_positions(
        chord: Chord,
        positions_data: list[ChordPositionCreateDict],
    ) -> None:
        """Create positions for the chord.

        Args:
            chord (Chord): existing chord
            positions_data (list[ChordPositionCreateDict]): position data for the chord
        """
        chord.positions.all().delete()
        positions = [ChordPosition(chord=chord, **pos) for pos in positions_data]
        ChordPosition.objects.bulk_create(positions)
