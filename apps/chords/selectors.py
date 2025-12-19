# SPDX-FileCopyrightText: 2025 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Selectors for the chords app."""

from django.db.models import QuerySet

from .models import Chord


def get_full_chord_by_id(*, chord_id: int) -> Chord:
    """Get a single Chord object by ID.

    Args:
        chord_id (int): The primary key of the Chord.

    Returns:
        Chord: The optimized Chord instance.

    Raises:
        Chord.DoesNotExist: If the chord with the given ID is not found.
    """
    return Chord.objects.select_related().prefetch_related("positions").get(id=chord_id)


def get_all_chords() -> QuerySet[Chord]:
    """Get a QuerySet of all Chord objects with positions.

    Returns:
        QuerySet[Chord]: Optimized QuerySet of all chords ordered by
            order_in_note and title.
    """
    return (
        Chord.objects.all()
        .order_by("title", "order_in_note")
        .prefetch_related("positions")
    )
