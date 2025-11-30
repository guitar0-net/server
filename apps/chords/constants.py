# SPDX-FileCopyrightText: 2025 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Module-level constants for guitar chords rules."""

from typing import Final

MIN_STRING_NUMBER: Final[int] = 1
"""Minimum guitar string number (1-indexed)."""

MAX_STRING_NUMBER: Final[int] = 6
"""Maximum guitar string number for standard guitars."""

MIN_FRET: Final[int] = -1
"""Minimum fret value (-1 for muted string, 0 - for open string)."""

MAX_FRET: Final[int] = 12
"""Maximum practical fret for chord positions (can be adjusted for extended ranges)."""

MIN_FINGER: Final[int] = 0
"""Minimum finger value (0 for not used)."""

MAX_FINGER: Final[int] = 4
"""Maximum finger value (1-4 for fingers, 0 for open)."""
