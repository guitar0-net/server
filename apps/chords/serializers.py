# SPDX-FileCopyrightText: 2025 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Serializers for the chords app."""

from rest_framework import serializers

from apps.chords.constants import MAX_STRING_NUMBER
from apps.chords.models import Chord, ChordPosition


class ChordPositionSerializer(serializers.ModelSerializer[ChordPosition]):
    """Serializer for one string position."""

    class Meta:
        model = ChordPosition
        fields = ("string_number", "fret", "finger")


class ChordCreateUpdateSerializer(serializers.ModelSerializer[Chord]):
    """Input serializer."""

    positions = ChordPositionSerializer(many=True, required=True)

    class Meta:
        model = Chord
        fields = (
            "title",
            "musical_title",
            "order_in_note",
            "start_fret",
            "has_barre",
            "positions",
        )

    @staticmethod
    def validate_positions(value: list[dict[str, int]]) -> list[dict[str, int]]:
        """Check for duplicate strings in the request."""
        string_numbers = [item["string_number"] for item in value]
        if len(string_numbers) != len(set(string_numbers)):
            raise serializers.ValidationError(
                "Duplicate string numbers are not allowed."
            )
        if len(value) != MAX_STRING_NUMBER:
            raise serializers.ValidationError("Chord must has only 6 positions.")
        return value


class ChordOutputSerializer(serializers.ModelSerializer[Chord]):
    """Output serializer.

    Used for reading data
    """

    positions = ChordPositionSerializer(many=True, read_only=True)

    class Meta:
        model = Chord
        fields = (
            "id",
            "title",
            "musical_title",
            "order_in_note",
            "start_fret",
            "has_barre",
            "positions",
        )
