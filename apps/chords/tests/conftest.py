# SPDX-FileCopyrightText: 2025 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Pytest configuration and fixtures for testing chords app."""

import pytest

from apps.chords.models import Chord, ChordPosition
from apps.chords.tests.factories import (
    ChordFactory,
    ChordPositionFactory,
    FullChordFactory,
)


@pytest.fixture
def chord_factory() -> type[FullChordFactory]:
    """Fixture providing the FullChord Factory for creating chords in tests."""
    return FullChordFactory


@pytest.fixture
def chord() -> Chord:
    """Fixture creating a chord for testing.

    Returns:
        Chord: chord instance without chord positions
    """
    return ChordFactory.create()


@pytest.fixture
def chord_position() -> ChordPosition:
    """Fixture creating one chord position.

    Returns:
        ChordPosition: a string, a fret and a finger
    """
    return ChordPositionFactory.create()
