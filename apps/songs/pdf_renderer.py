# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""PDF renderer for song print view."""

from typing import Literal, TypedDict

from django.template.loader import render_to_string
from markdownx.utils import markdownify  # type: ignore[import-untyped]
from weasyprint import HTML  # type: ignore[import-untyped]

from apps.songs.models import Song

type Size = Literal[1, 2, 3, 4, 5]
type Orientation = Literal["vertical", "horizontal"]


class PrintSettings(TypedDict):
    """Validated print settings passed from the request serializer."""

    show_chords: bool
    show_schemes: bool
    show_text: bool
    chord_orientation: Orientation
    chord_size: Size
    scheme_size: Size
    text_size: Size
    columns_count: int


_CHORD_WIDTHS: dict[Orientation, dict[Size, str]] = {
    "vertical": {
        1: "16.66%",
        2: "20%",
        3: "25%",
        4: "33.33%",
        5: "50%",
    },
    "horizontal": {
        1: "33.33%",
        2: "50%",
        3: "66.66%",
        4: "80%",
        5: "100%",
    },
}

_SCHEME_WIDTHS: dict[Size, str] = {
    1: "30%",
    2: "40%",
    3: "55%",
    4: "70%",
    5: "85%",
}

_LABEL_SIZES: dict[Size, str] = {
    1: "8pt",
    2: "9pt",
    3: "10.5pt",
    4: "12pt",
    5: "14pt",
}

_FONT_SIZES: dict[Size, str] = {
    1: "10pt",
    2: "12pt",
    3: "14pt",
    4: "16pt",
    5: "18pt",
}


def render_song_pdf(song: Song, settings: PrintSettings) -> bytes:
    """Render a Song to PDF bytes applying the given print settings."""
    chords = []
    if settings["show_chords"]:
        for chord in song.chords.all():
            svg = (
                chord.svg_vertical
                if settings["chord_orientation"] == "vertical"
                else chord.svg_horizontal
            )
            if svg:
                chords.append({"title": chord.title, "svg": svg})

    schemes: list[dict[str, str]] = []
    if settings["show_schemes"]:
        schemes.extend(
            {
                "path": f"file://{scheme.image.path}",
                "inscription": scheme.inscription,
            }
            for scheme in song.schemes.all()
            if scheme.image
        )

    text_html = ""
    if settings["show_text"] and song.text:
        text_html = markdownify(song.text)

    context = {
        "song_title": song.title,
        "chords": chords,
        "schemes": schemes,
        "text_html": text_html,
        "columns_count": settings["columns_count"],
        "chord_width": _CHORD_WIDTHS[settings["chord_orientation"]][
            settings["chord_size"]
        ],
        "chord_label_size": _LABEL_SIZES[settings["chord_size"]],
        "scheme_width": _SCHEME_WIDTHS[settings["scheme_size"]],
        "scheme_caption_size": _LABEL_SIZES[settings["scheme_size"]],
        "text_font_size": _FONT_SIZES[settings["text_size"]],
    }

    html_string = render_to_string("songs/song_print.html", context)
    return HTML(string=html_string).write_pdf()  # type: ignore[no-any-return]
