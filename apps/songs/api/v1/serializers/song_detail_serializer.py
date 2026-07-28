# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Serializers for the songs app."""

from rest_framework import serializers

from apps.chords.api.v1.serializers.chord_embedded_serializer import (
    ChordEmbeddedSerializer,
)
from apps.schemes.api.v1.serializers.image_scheme_serializer import (
    ImageSchemeSerializer,
)
from apps.songs.models import Song


class SongDetailSerializer(serializers.ModelSerializer[Song]):
    """Song detail serializer."""

    chords = ChordEmbeddedSerializer(many=True, read_only=True)
    schemes = ImageSchemeSerializer(many=True, read_only=True)

    class Meta:
        model = Song
        fields = ("uuid", "title", "text", "metronome", "schemes", "chords")
