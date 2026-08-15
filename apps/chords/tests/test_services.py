# SPDX-FileCopyrightText: 2025-2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from collections.abc import Iterable
from datetime import UTC, datetime

import pytest

from apps.chords import services as chord_services
from apps.chords.models import Chord, ChordPosition
from apps.chords.services import ChordCreateDict, ChordPositionCreateDict, ChordService
from apps.chords.tests.factories import FullChordFactory
from apps.lessons.models import Lesson
from apps.lessons.tests.factories import LessonFactory
from apps.songs.tests.factories import SongFactory


@pytest.mark.django_db
def test_create_chord_success() -> None:
    chord_fields: ChordCreateDict = {
        "title": "Am",
        "musical_title": "A minor",
        "order_in_note": 1,
        "start_fret": 1,
        "has_barre": False,
    }

    positions: list[ChordPositionCreateDict] = [
        {"string_number": 1, "fret": 1, "finger": 1},
        {"string_number": 2, "fret": 2, "finger": 2},
        {"string_number": 3, "fret": 2, "finger": 3},
        {"string_number": 4, "fret": 2, "finger": 4},
        {"string_number": 5, "fret": 2, "finger": 0},
        {"string_number": 6, "fret": 2, "finger": 0},
    ]

    chord = ChordService.create_chord(positions=positions, chord_fields=chord_fields)

    assert chord.pk is not None
    assert Chord.objects.count() == 1
    assert ChordPosition.objects.count() == 6

    created_positions = list(chord.positions.order_by("string_number"))
    assert created_positions[0].fret == 1
    assert created_positions[1].finger == 2


@pytest.mark.django_db
def test_create_chord_fail_when_not_enough_positions() -> None:
    chord_fields: ChordCreateDict = {
        "title": "Am",
        "musical_title": "A minor",
        "order_in_note": 1,
        "start_fret": 1,
        "has_barre": False,
    }

    positions: list[ChordPositionCreateDict] = [
        {"string_number": 1, "fret": 1, "finger": 1},
        {"string_number": 2, "fret": 2, "finger": 2},
    ]

    with pytest.raises(ValueError, match="Chord must have exactly 6 positions"):
        ChordService.create_chord(positions=positions, chord_fields=chord_fields)


@pytest.mark.django_db
def test_update_chord_without_positions(chord_factory: type[FullChordFactory]) -> None:
    chord = chord_factory.create(
        title="Am",
        musical_title="A minor",
        order_in_note=1,
        start_fret=1,
        has_barre=False,
    )

    update_data = {
        "title": "Am7",
        "start_fret": 2,
    }

    updated = ChordService.update_chord(chord=chord, data=update_data)

    assert updated.title == "Am7"
    assert updated.start_fret == 2
    assert ChordPosition.objects.count() == 6


@pytest.mark.django_db
def test_update_chord_with_positions_replaces_old(
    chord_factory: type[FullChordFactory],
) -> None:
    chord = chord_factory.create(
        title="Am",
        musical_title="A minor",
        order_in_note=1,
        start_fret=1,
        has_barre=False,
    )

    new_positions = [
        {"string_number": 3, "fret": 4, "finger": 2},
        {"string_number": 4, "fret": 5, "finger": 3},
        {"string_number": 1, "fret": 5, "finger": 3},
        {"string_number": 2, "fret": 5, "finger": 3},
        {"string_number": 5, "fret": 5, "finger": 3},
        {"string_number": 6, "fret": 5, "finger": 3},
    ]

    update_data = {
        "title": "Am6",
        "positions": new_positions,
    }

    updated = ChordService.update_chord(chord=chord, data=update_data)

    assert updated.title == "Am6"
    assert ChordPosition.objects.count() == 6

    created_positions = sorted(updated.positions.all(), key=lambda x: x.string_number)
    assert created_positions[0].fret == 5
    assert created_positions[1].finger == 3


@pytest.mark.django_db
def test_update_chord_fail_when_not_enough_positions(
    chord_factory: type[FullChordFactory],
) -> None:
    chord = chord_factory.create()
    positions: list[ChordPositionCreateDict] = [
        {"string_number": 1, "fret": 1, "finger": 1},
        {"string_number": 2, "fret": 2, "finger": 2},
    ]
    update_data = {
        "title": "Am6",
        "positions": positions,
    }

    with pytest.raises(ValueError, match="Chord must have exactly 6 positions"):
        ChordService.update_chord(chord=chord, data=update_data)


@pytest.mark.django_db
def test_delete_chord(chord_factory: type[FullChordFactory]) -> None:
    chord = chord_factory.create()

    ChordService.delete_chord(chord=chord)

    assert Chord.objects.count() == 0
    assert ChordPosition.objects.count() == 0


@pytest.mark.django_db
def test_delete_chord_with_none_pk(chord_factory: type[FullChordFactory]) -> None:
    chord = chord_factory.build()

    ChordService.delete_chord(chord=chord)


@pytest.mark.django_db
def test_replace_positions_creates_positions(chord: Chord) -> None:
    positions_data: list[ChordPositionCreateDict] = [
        {"string_number": 1, "fret": 0, "finger": 0},
        {"string_number": 2, "fret": 1, "finger": 1},
        {"string_number": 3, "fret": 2, "finger": 2},
    ]

    ChordService._replace_positions(chord, positions_data)

    positions = list(chord.positions.all())
    assert len(positions) == 3

    for data, pos in zip(positions_data, positions, strict=True):
        assert pos.string_number == data["string_number"]
        assert pos.fret == data["fret"]
        assert pos.finger == data["finger"]


@pytest.mark.django_db
def test_replace_positions_replaces_existing(chord: Chord) -> None:
    old_positions = [
        ChordPosition.objects.create(chord=chord, string_number=i, fret=i, finger=i)
        for i in range(1, 4)
    ]
    new_positions_data: list[ChordPositionCreateDict] = [
        {"string_number": 1, "fret": 0, "finger": 0},
        {"string_number": 2, "fret": 1, "finger": 1},
    ]

    ChordService._replace_positions(chord, new_positions_data)

    for old in old_positions:
        assert not ChordPosition.objects.filter(pk=old.pk).exists()

    positions = list(chord.positions.all())
    assert len(positions) == len(new_positions_data)
    for data, pos in zip(new_positions_data, positions, strict=True):
        assert pos.string_number == data["string_number"]
        assert pos.fret == data["fret"]
        assert pos.finger == data["finger"]


@pytest.mark.django_db
def test_create_chord_sets_svg_horizontal() -> None:
    chord_fields: ChordCreateDict = {
        "title": "G",
        "musical_title": "G major",
        "order_in_note": 1,
        "start_fret": 1,
        "has_barre": False,
    }
    positions: list[ChordPositionCreateDict] = [
        {"string_number": 1, "fret": 2, "finger": 1},
        {"string_number": 2, "fret": 3, "finger": 2},
        {"string_number": 3, "fret": 0, "finger": 0},
        {"string_number": 4, "fret": 0, "finger": 0},
        {"string_number": 5, "fret": 2, "finger": 3},
        {"string_number": 6, "fret": 3, "finger": 4},
    ]

    chord = ChordService.create_chord(positions=positions, chord_fields=chord_fields)

    assert chord.svg_horizontal


@pytest.mark.django_db
def test_create_chord_sets_svg_vertical() -> None:
    chord_fields: ChordCreateDict = {
        "title": "G",
        "musical_title": "G major",
        "order_in_note": 1,
        "start_fret": 1,
        "has_barre": False,
    }
    positions: list[ChordPositionCreateDict] = [
        {"string_number": 1, "fret": 2, "finger": 1},
        {"string_number": 2, "fret": 3, "finger": 2},
        {"string_number": 3, "fret": 0, "finger": 0},
        {"string_number": 4, "fret": 0, "finger": 0},
        {"string_number": 5, "fret": 2, "finger": 3},
        {"string_number": 6, "fret": 3, "finger": 4},
    ]

    chord = ChordService.create_chord(positions=positions, chord_fields=chord_fields)

    assert chord.svg_vertical


@pytest.mark.django_db
def test_update_chord_sets_svg_horizontal(
    chord_factory: type[FullChordFactory],
) -> None:
    chord = chord_factory.create(
        title="Am",
        musical_title="A minor",
        order_in_note=1,
        start_fret=1,
        has_barre=False,
    )
    new_positions = [
        {"string_number": 1, "fret": 1, "finger": 1},
        {"string_number": 2, "fret": 2, "finger": 2},
        {"string_number": 3, "fret": 2, "finger": 3},
        {"string_number": 4, "fret": 0, "finger": 0},
        {"string_number": 5, "fret": -1, "finger": 0},
        {"string_number": 6, "fret": -1, "finger": 0},
    ]

    updated = ChordService.update_chord(chord=chord, data={"positions": new_positions})

    assert updated.svg_horizontal


@pytest.mark.django_db
def test_update_chord_sets_svg_vertical(chord_factory: type[FullChordFactory]) -> None:
    chord = chord_factory.create(
        title="Am",
        musical_title="A minor",
        order_in_note=1,
        start_fret=1,
        has_barre=False,
    )
    new_positions = [
        {"string_number": 1, "fret": 1, "finger": 1},
        {"string_number": 2, "fret": 2, "finger": 2},
        {"string_number": 3, "fret": 2, "finger": 3},
        {"string_number": 4, "fret": 0, "finger": 0},
        {"string_number": 5, "fret": -1, "finger": 0},
        {"string_number": 6, "fret": -1, "finger": 0},
    ]

    updated = ChordService.update_chord(chord=chord, data={"positions": new_positions})

    assert updated.svg_vertical


@pytest.mark.django_db
def test_replace_positions_empty_list(chord: Chord) -> None:
    for i in range(1, 4):
        ChordPosition.objects.create(chord=chord, string_number=i, fret=i, finger=i)

    ChordService._replace_positions(chord, [])

    assert chord.positions.count() == 0


@pytest.mark.django_db
def test_save_chord_propagates_updated_at_to_lessons_using_the_chord() -> None:
    stale = datetime(2026, 3, 1, tzinfo=UTC)
    chord = FullChordFactory.create(title="Cadd9")
    lesson = LessonFactory.create(
        songs=[SongFactory.create(title="Тиша над Дніпром", chords=[chord])]
    )
    Lesson.objects.filter(pk=lesson.pk).update(updated_at=stale)

    ChordService.save_chord(chord=chord)

    lesson.refresh_from_db()
    assert lesson.updated_at > stale


@pytest.mark.django_db
def test_save_chord_leaves_lessons_alone_when_nothing_visible_changed() -> None:
    stale = datetime(2026, 3, 7, tzinfo=UTC)
    chord = FullChordFactory.create(title="Asus2")
    lesson = LessonFactory.create(
        songs=[SongFactory.create(title="Роса на світанку", chords=[chord])]
    )
    ChordService.save_chord(chord=chord)
    Lesson.objects.filter(pk=lesson.pk).update(updated_at=stale)

    ChordService.save_chord(chord=chord)

    lesson.refresh_from_db()
    assert lesson.updated_at == stale


@pytest.mark.django_db
def test_save_chord_propagates_a_field_edit_that_leaves_the_svg_identical() -> None:
    stale = datetime(2026, 3, 8, tzinfo=UTC)
    chord = FullChordFactory.create(title="Gadd11", musical_title="Соль з ундецимою")
    lesson = LessonFactory.create(
        songs=[SongFactory.create(title="Стежка до криниці", chords=[chord])]
    )
    ChordService.save_chord(chord=chord)
    Lesson.objects.filter(pk=lesson.pk).update(updated_at=stale)
    chord.musical_title = "Соль-мажор з ундецимою"

    ChordService.save_chord(chord=chord)

    lesson.refresh_from_db()
    assert lesson.updated_at > stale


@pytest.mark.django_db
def test_bulk_regenerate_svgs_propagates_updated_at_to_lessons() -> None:
    stale = datetime(2026, 3, 2, tzinfo=UTC)
    chord = FullChordFactory.create(title="Gsus4")
    lesson = LessonFactory.create(
        songs=[SongFactory.create(title="Журавлі летять", chords=[chord])]
    )
    Lesson.objects.filter(pk=lesson.pk).update(updated_at=stale)

    ChordService.bulk_regenerate_svgs()

    lesson.refresh_from_db()
    assert lesson.updated_at > stale


@pytest.mark.django_db
def test_delete_chord_stamps_lessons_before_the_relation_disappears() -> None:
    stale = datetime(2026, 3, 3, tzinfo=UTC)
    chord = FullChordFactory.create(title="Bm7")
    lesson = LessonFactory.create(
        songs=[SongFactory.create(title="Остання пісня", chords=[chord])]
    )
    Lesson.objects.filter(pk=lesson.pk).update(updated_at=stale)

    ChordService.delete_chord(chord=chord)

    lesson.refresh_from_db()
    assert lesson.updated_at > stale


@pytest.mark.django_db
def test_update_chord_propagates_updated_at_to_lessons_using_the_chord() -> None:
    stale = datetime(2026, 3, 4, tzinfo=UTC)
    chord = FullChordFactory.create(title="Fmaj7")
    lesson = LessonFactory.create(
        songs=[SongFactory.create(title="Криниця біля хати", chords=[chord])]
    )
    Lesson.objects.filter(pk=lesson.pk).update(updated_at=stale)

    ChordService.update_chord(chord=chord, data={"musical_title": "Фа-мажор сьомий"})

    lesson.refresh_from_db()
    assert lesson.updated_at > stale


@pytest.mark.django_db
def test_bulk_regenerate_svgs_leaves_lessons_alone_when_no_svg_changed() -> None:
    stale = datetime(2026, 3, 5, tzinfo=UTC)
    chord = FullChordFactory.create(title="Ddim7")
    lesson = LessonFactory.create(
        songs=[SongFactory.create(title="Вітер зі сходу", chords=[chord])]
    )
    ChordService.bulk_regenerate_svgs()
    Lesson.objects.filter(pk=lesson.pk).update(updated_at=stale)

    ChordService.bulk_regenerate_svgs()

    lesson.refresh_from_db()
    assert lesson.updated_at == stale


@pytest.mark.django_db
def test_bulk_regenerate_svgs_discards_the_svgs_when_propagation_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def refuse(chord_ids: Iterable[int]) -> int:
        raise RuntimeError("зв'язок з уроками недоступний")

    chord = FullChordFactory.create(title="Ebmaj7")
    monkeypatch.setattr(chord_services, "touch_lessons_for_chords", refuse)

    with pytest.raises(RuntimeError):
        ChordService.bulk_regenerate_svgs()

    chord.refresh_from_db()
    assert not chord.svg_horizontal


@pytest.mark.django_db
def test_delete_chords_stamps_lessons_before_the_relation_disappears() -> None:
    stale = datetime(2026, 3, 6, tzinfo=UTC)
    chords = FullChordFactory.create_batch(2)
    lesson = LessonFactory.create(
        songs=[SongFactory.create(title="Полонина вранці", chords=chords)]
    )
    Lesson.objects.filter(pk=lesson.pk).update(updated_at=stale)

    ChordService.delete_chords(chords=Chord.objects.all())

    lesson.refresh_from_db()
    assert lesson.updated_at > stale
