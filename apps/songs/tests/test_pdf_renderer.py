# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for songs PDF renderer."""

import pytest

from apps.chords.tests.factories import ChordFactory
from apps.songs.models import Song
from apps.songs.pdf_renderer import Orientation, PrintSettings, Size, render_song_pdf
from apps.songs.tests.factories import SongFactory


def _default_settings(  # noqa: PLR0913
    *,
    show_chords: bool = True,
    show_schemes: bool = True,
    show_text: bool = True,
    chord_orientation: Orientation = "vertical",
    chord_size: Size = 3,
    scheme_size: Size = 3,
    text_size: Size = 3,
    columns_count: int = 1,
) -> PrintSettings:
    return PrintSettings(
        show_chords=show_chords,
        show_schemes=show_schemes,
        show_text=show_text,
        chord_orientation=chord_orientation,
        chord_size=chord_size,
        scheme_size=scheme_size,
        text_size=text_size,
        columns_count=columns_count,
    )


def _song_with_drawn_chords(count: int) -> Song:
    return SongFactory.create(
        title="Ой, то не вечер",
        chords=[
            ChordFactory.create(
                title=f"Аккорд {index}",
                svg_vertical=(
                    '<svg viewBox="0 0 91 214" xmlns="http://www.w3.org/2000/svg">'
                    '<rect x="0" y="0" width="91" height="214" fill="none" '
                    'stroke="currentColor"/></svg>'
                ),
            )
            for index in range(count)
        ],
    )


@pytest.mark.integration
@pytest.mark.django_db
def test_render_song_pdf_returns_bytes() -> None:
    song = SongFactory.create(text="Lyrics line одна")
    result = render_song_pdf(song, _default_settings())
    assert isinstance(result, bytes)


@pytest.mark.integration
@pytest.mark.django_db
def test_render_song_pdf_output_is_valid_pdf() -> None:
    song = SongFactory.create(text="Текст с аккордами [Am] тест")
    result = render_song_pdf(song, _default_settings())
    assert result[:4] == b"%PDF"


@pytest.mark.integration
@pytest.mark.django_db
def test_render_song_pdf_with_show_text_false_returns_pdf() -> None:
    song = SongFactory.create()
    result = render_song_pdf(song, _default_settings(show_text=False))
    assert result[:4] == b"%PDF"


@pytest.mark.integration
@pytest.mark.django_db
def test_render_song_pdf_with_show_chords_false_returns_pdf() -> None:
    song = SongFactory.create(chords=1)
    result = render_song_pdf(song, _default_settings(show_chords=False))
    assert result[:4] == b"%PDF"


@pytest.mark.integration
@pytest.mark.django_db
def test_render_song_pdf_with_horizontal_orientation_returns_pdf() -> None:
    song = SongFactory.create()
    result = render_song_pdf(song, _default_settings(chord_orientation="horizontal"))
    assert result[:4] == b"%PDF"


@pytest.mark.integration
@pytest.mark.django_db
def test_render_song_pdf_with_three_columns_returns_pdf() -> None:
    song = SongFactory.create(text="Куплет первый\n\nКуплет второй\n\nКуплет третий")
    result = render_song_pdf(song, _default_settings(columns_count=3))
    assert result[:4] == b"%PDF"


@pytest.mark.integration
@pytest.mark.django_db
def test_render_song_pdf_with_xl_sizes_returns_pdf() -> None:
    song = SongFactory.create()
    result = render_song_pdf(
        song,
        _default_settings(chord_size=5, scheme_size=5, text_size=5),
    )
    assert result[:4] == b"%PDF"


@pytest.mark.integration
@pytest.mark.django_db
def test_render_song_pdf_with_xs_sizes_returns_pdf() -> None:
    song = SongFactory.create()
    result = render_song_pdf(
        song,
        _default_settings(chord_size=1, scheme_size=1, text_size=1),
    )
    assert result[:4] == b"%PDF"


@pytest.mark.integration
@pytest.mark.django_db
def test_render_song_pdf_grows_with_chord_size() -> None:
    song = _song_with_drawn_chords(8)
    smallest = render_song_pdf(song, _default_settings(chord_size=1))
    largest = render_song_pdf(song, _default_settings(chord_size=5))
    assert len(largest) > len(smallest)
