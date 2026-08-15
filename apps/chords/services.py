# SPDX-FileCopyrightText: 2025 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Services for the chords app."""

from typing import Any, TypedDict

from django.db import transaction
from django.db.models import QuerySet

from apps.lessons.services import touch_lessons_for_chords

from .constants import MAX_STRING_NUMBER
from .models import Chord, ChordPosition
from .selectors import get_all_chords, get_chord_sync_state
from .svg_renderer import render_chord_svg


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
        if len(positions) != MAX_STRING_NUMBER:
            raise ValueError("Chord must have exactly 6 positions")

        chord = Chord.objects.create(**chord_fields)
        ChordService._replace_positions(chord, positions)
        chord.svg_horizontal, chord.svg_vertical = render_chord_svg(chord)
        chord.save(update_fields=["svg_horizontal", "svg_vertical"])
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
        if positions_data is not None and len(positions_data) != MAX_STRING_NUMBER:
            raise ValueError("Chord must have exactly 6 positions")

        for field, value in data.items():
            setattr(chord, field, value)
        chord.save()

        if positions_data is not None:
            ChordService._replace_positions(chord, positions_data)

        chord.svg_horizontal, chord.svg_vertical = render_chord_svg(chord)
        chord.save(update_fields=["svg_horizontal", "svg_vertical"])
        touch_lessons_for_chords([chord.pk])
        return chord

    @staticmethod
    @transaction.atomic
    def save_chord(*, chord: Chord) -> None:
        """Persist a chord with a freshly rendered SVG, propagating real changes.

        Serves the admin, which must re-render after the position inlines are
        saved. The related lessons are stamped only when the state exposed to
        clients actually moved: an admin pressing Save with nothing edited
        would otherwise push most of the catalogue past `since` and turn the
        next delta sync into a full download for every client.
        """
        before = get_chord_sync_state(chord.pk) if chord.pk is not None else None
        chord.svg_horizontal, chord.svg_vertical = render_chord_svg(chord)
        chord.save()
        if before != get_chord_sync_state(chord.pk):
            touch_lessons_for_chords([chord.pk])

    @staticmethod
    def bulk_regenerate_svgs() -> int:
        """Regenerate SVG fields for all chords. Returns count of updated chords.

        Only chords whose rendered output actually differs are written and
        propagated. Re-rendering is deterministic, so a repeat run is normally
        a no-op — stamping every lesson regardless would move the whole
        catalogue past `since` and turn each delta sync into a full download.

        Rendering runs outside the transaction; only the write and the
        propagation share one. They have to, because that skip-unchanged rule
        makes a half-applied run unrepairable: committing the SVGs without the
        stamps leaves a re-run seeing `rendered == stored`, finding nothing to
        change, and never propagating at all. Rendering carries no such
        constraint, and keeping the whole catalogue's render inside the
        transaction would hold row locks for its entire duration.
        """
        changed = []
        for chord in get_all_chords():
            horizontal, vertical = render_chord_svg(chord)
            if (horizontal, vertical) == (chord.svg_horizontal, chord.svg_vertical):
                continue
            chord.svg_horizontal, chord.svg_vertical = horizontal, vertical
            changed.append(chord)

        with transaction.atomic():
            Chord.objects.bulk_update(changed, ["svg_horizontal", "svg_vertical"])
            touch_lessons_for_chords([chord.pk for chord in changed])
        return len(changed)

    @staticmethod
    @transaction.atomic
    def delete_chord(*, chord: Chord) -> None:
        """Delete a Chord instance.

        Args:
            chord (Chord): The Chord instance to delete.
        """
        if chord.pk is not None:
            # Order matters: the song-to-chord rows that identify the affected
            # lessons disappear with the chord, so they must be stamped first.
            touch_lessons_for_chords([chord.pk])
            chord.delete()

    @staticmethod
    @transaction.atomic
    def delete_chords(*, chords: QuerySet[Chord]) -> None:
        """Delete every chord in the queryset, propagating to related lessons.

        Serves the admin bulk action, which never routes through
        `delete_chord`. Same ordering constraint: the song-to-chord rows are
        read before `delete()` drops them.
        """
        touch_lessons_for_chords(list(chords.values_list("pk", flat=True)))
        chords.delete()

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
