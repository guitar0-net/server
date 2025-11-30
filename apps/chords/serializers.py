# SPDX-FileCopyrightText: 2025 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Serializers for the chords app."""

from typing import Any

from django.db import transaction
from rest_framework import serializers

from apps.chords.models import Chord, ChordPosition


class ChordPositionSerializer(serializers.ModelSerializer[ChordPosition]):
    """Serializer for one string position."""

    class Meta:
        model = ChordPosition
        fields = ("string_number", "fret", "finger")


class ChordSerializer(serializers.ModelSerializer[Chord]):
    """Serializer for a chord with nested для аккорда с вложенными позициями струн."""

    positions = ChordPositionSerializer(many=True)

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
        read_only_fields = ("id",)

    @staticmethod
    def create(validated_data: dict[str, Any]) -> Chord:
        """Create a new Chord."""
        positions_data = validated_data.pop("positions", [])

        with transaction.atomic():
            chord = Chord.objects.create(**validated_data)
            ChordPosition.objects.bulk_create([
                ChordPosition(chord=chord, **pos) for pos in positions_data
            ])

        return chord

    def update(self, instance: Chord, validated_data: dict[str, Any]) -> Chord:
        """Update a Chord."""
        positions_data = validated_data.pop("positions", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if positions_data is not None:
            instance.positions.all().delete()  # pyright: ignore[reportAttributeAccessIssue]
            self._create_positions(instance, positions_data)
        return instance

    @staticmethod
    def _create_positions(chord: Chord, positions_data: list[dict[str, Any]]) -> None:
        """Create positions with proper validation."""
        for pos_data in positions_data:
            pos_data["chord"] = chord
            pos_serializer = ChordPositionSerializer(data=pos_data)
            pos_serializer.is_valid(raise_exception=True)
            pos_serializer.save(chord=chord)
