# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later


import pytest

from apps.chords.tests.factories import ChordFactory
from apps.schemes.tests.factories import ImageSchemeFactory
from apps.songs.api.v1.serializers.song_detail_serializer import SongDetailSerializer
from apps.songs.api.v1.serializers.songs_list_serializer import SongListSerializer
from apps.songs.tests.factories import SongFactory


@pytest.mark.django_db
def test_song_list_serializer() -> None:
    song = SongFactory.create(title="Test Song")

    data = SongListSerializer(song).data

    assert data == {"uuid": str(song.uuid), "title": "Test Song"}


@pytest.mark.django_db
def test_song_detail_serializer() -> None:
    schemes = ImageSchemeFactory.create_batch(
        2,
        height=100,
        width=200,
    )
    chords = ChordFactory.create_batch(1)

    song = SongFactory.create(
        title="Song 1",
        text="song text",
        metronome=80,
        chords=chords,
        schemes=schemes,
    )

    data = SongDetailSerializer(song).data

    assert data["uuid"] == str(song.uuid)
    assert data["title"] == "Song 1"
    assert data["text"] == "song text"
    assert data["metronome"] == 80

    assert len(data["schemes"]) == 2
    assert {s["id"] for s in data["schemes"]} == {s.pk for s in schemes}

    assert len(data["chords"]) == 1
    chord_data = data["chords"][0]
    assert chord_data["id"] == chords[0].id
    assert chord_data["title"] == chords[0].title
    assert "positions" not in chord_data
