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


def get_chords_with_positions(
    *, title_contains: str | None = None, has_barre: bool | None = None
) -> QuerySet[Chord]:
    """Get an QuerySet of Chord objects and optional filtering.

    Args:
        title_contains (Optional[str]): Filters chords where the title contains this
          string (case-insensitive).
        has_barre (Optional[bool]): Filters chords based on whether they require a barre

    Returns:
        QuerySet[Chord]: Optimized and filtered QuerySet.
    """
    qs = Chord.objects.all().order_by("order_in_note", "title")

    qs = qs.prefetch_related("positions")

    if title_contains:
        qs = qs.filter(title__icontains=title_contains)

    if has_barre is not None:
        qs = qs.filter(has_barre=has_barre)

    return qs
