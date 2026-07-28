# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Serializer for a chord embedded inside a song."""

from rest_framework import serializers

from apps.chords.models import Chord


class ChordEmbeddedSerializer(serializers.ModelSerializer[Chord]):
    """Chord representation for nesting inside a song.

    Omits `positions` — clients render chord diagrams from the pre-rendered
    `svg_horizontal`/`svg_vertical` fields, never from raw string positions
    (same choice already made by `ChordSyncSerializer` for offline sync).
    Keeping it out here avoids prefetching `positions` for every chord in
    every song of a lesson.
    """

    class Meta:
        model = Chord
        fields = (
            "id",
            "title",
            "musical_title",
            "order_in_note",
            "start_fret",
            "has_barre",
            "svg_horizontal",
            "svg_vertical",
        )
