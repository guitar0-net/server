# SPDX-FileCopyrightText: 2025 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Models for the chords app."""

from typing import ClassVar

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.chords.constants import (
    MAX_FINGER,
    MAX_FRET,
    MAX_STRING_NUMBER,
    MIN_FINGER,
    MIN_FRET,
    MIN_STRING_NUMBER,
)


class Chord(models.Model):
    """Main model for saving information about guitar chords."""

    title = models.CharField("Название", max_length=50)
    musical_title = models.CharField("Музыкальное название", max_length=50)
    order_in_note = models.PositiveSmallIntegerField("Порядок отображения", default=1)
    start_fret = models.PositiveSmallIntegerField("С какого лада начинается", default=1)
    has_barre = models.BooleanField("Есть барре?", default=False)

    def __str__(self) -> str:
        return self.title if not self.has_barre else f"{self.title} bare"


class ChordPosition(models.Model):
    """Model for describing position of one string in a chord."""

    chord = models.ForeignKey(Chord, related_name="positions", on_delete=models.CASCADE)
    string_number = models.PositiveSmallIntegerField(
        verbose_name="Номер струны",
        validators=[
            MinValueValidator(MIN_STRING_NUMBER),
            MaxValueValidator(MAX_STRING_NUMBER),
        ],
    )
    fret = models.SmallIntegerField(
        verbose_name="На каком ладу зажата",
        validators=[
            MinValueValidator(MIN_FRET),
            MaxValueValidator(MAX_FRET),
        ],
        help_text="0 - открыта, -1 - заглушена",
    )
    finger = models.SmallIntegerField(
        verbose_name="Каким пальцем зажата",
        validators=[
            MinValueValidator(MIN_FINGER),
            MaxValueValidator(MAX_FINGER),
        ],
    )

    class Meta:
        constraints: ClassVar[list] = [  # type: ignore[type-arg]
            models.UniqueConstraint(
                fields=["chord", "string_number"],
                name="unique_chord_string_number",
            )
        ]
        ordering: ClassVar[list[str]] = ["string_number"]

    def __str__(self) -> str:
        return f"String #{self.string_number}: fret {self.fret}, finger {self.finger}"
