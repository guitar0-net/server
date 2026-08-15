# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for the sync serializers.

The change-detection guards below are the reason delta sync stays correct.
Chord and scheme edits do not touch any Lesson row on their own, so services
decide whether to stamp the related lessons by diffing the fields the sync
payload exposes, named in each app's `SYNC_FIELDS`. Those tuples are hand-kept
mirrors of the serializers here: let one drift and an edit to the new field is
read as "nothing changed", no lesson is stamped, and the field never reaches a
client — silently, and with every other test still green.
"""

from apps.chords.selectors import SYNC_FIELDS as CHORD_SYNC_FIELDS
from apps.schemes.selectors import SYNC_FIELDS as SCHEME_SYNC_FIELDS
from apps.sync.api.v1.serializers.sync_serializers import (
    ChordSyncSerializer,
    SchemeSyncSerializer,
)


def test_chord_sync_state_covers_every_serialized_field() -> None:
    # `id` is excluded: it is the identity of the row, never an edit to detect.
    serialized = {field for field in ChordSyncSerializer.Meta.fields if field != "id"}

    assert serialized == set(CHORD_SYNC_FIELDS)


def test_image_scheme_sync_state_covers_every_serialized_field() -> None:
    serialized = {field for field in SchemeSyncSerializer.Meta.fields if field != "id"}

    assert serialized == set(SCHEME_SYNC_FIELDS)
