# SPDX-FileCopyrightText: 2025 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Selectors for the chords app."""

from typing import Final

from django.db.models import QuerySet

from .models import Chord

SYNC_FIELDS: Final[tuple[str, ...]] = (
    "title",
    "musical_title",
    "order_in_note",
    "start_fret",
    "has_barre",
    "svg_horizontal",
    "svg_vertical",
)
"""Chord fields the sync payload exposes — must mirror `ChordSyncSerializer`.

Public because that mirroring is the contract, not an implementation detail:
`test_chord_sync_state_covers_every_serialized_field` fails the build if a
field is added to the serializer without being added here. Without that guard
the drift is silent — `get_chord_sync_state` would report "nothing changed"
for an edit to the new field, no lesson would be stamped, and the field would
never reach a delta-sync client.
"""


def get_chord_sync_state(chord_id: int) -> tuple[object, ...] | None:
    """Get the persisted values of every chord field the sync payload exposes.

    Services compare the state read before a write with the one read after it:
    only a difference is observable by a client, and only then is stamping the
    related lessons worth the full re-download it costs every one of them.

    Returns:
        tuple[object, ...] | None: Field values in declaration order, or None
            if no such chord exists.
    """
    return Chord.objects.filter(pk=chord_id).values_list(*SYNC_FIELDS).first()


def get_chord_by_id(chord_id: int) -> Chord | None:
    """Get a single Chord by ID with related data.

    Returns:
        Chord or None if not found.
    """
    return Chord.objects.filter(id=chord_id).prefetch_related("positions").first()


def get_all_chords() -> QuerySet[Chord]:
    """Get a QuerySet of all Chord objects with positions.

    Returns:
        QuerySet[Chord]: Optimized QuerySet of all chords ordered by
            order_in_note and title.
    """
    return (
        Chord.objects
        .all()
        .order_by("title", "order_in_note")
        .prefetch_related("positions")
    )
