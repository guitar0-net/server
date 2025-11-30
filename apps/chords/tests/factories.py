# SPDX-FileCopyrightText: 2025 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later


"""Factory for generating test Chord instances."""

import factory
from factory import Faker  # type: ignore[attr-defined]
from factory.django import DjangoModelFactory

from apps.chords.models import Chord, ChordPosition


class ChordFactory(DjangoModelFactory[Chord]):
    """Factory for creating Chord instances with realistic data."""

    title = Faker("word")
    musical_title = Faker("sentence", nb_words=2)
    order_in_note = Faker("pyint", min_value=1, max_value=10)
    start_fret = Faker("pyint", min_value=1, max_value=5)
    has_barre = Faker("boolean")

    class Meta:
        model = Chord


class ChordPositionFactory(DjangoModelFactory[ChordPosition]):
    """Factory for creating ChordPosition instances."""

    chord = factory.SubFactory(ChordFactory)  # pyright: ignore[reportPrivateImportUsage]
    string_number = factory.Sequence(lambda n: (n % 6) + 1)  # pyright: ignore[reportPrivateImportUsage]
    fret = Faker("pyint", min_value=-1, max_value=12)
    finger = Faker("pyint", min_value=0, max_value=4)

    class Meta:
        model = ChordPosition


class FullChordFactory(ChordFactory):
    """Factory that creates 6 string positions for a fully defined chord."""

    @factory.post_generation  # type: ignore[misc, attr-defined]
    def positions(
        self,
        create: bool,
        **kwargs: dict[str, str],
    ) -> None:
        if not create:
            return
        for string_num in range(1, 7):
            ChordPositionFactory(
                chord=self,
                string_number=string_num,
            )
