# SPDX-FileCopyrightText: 2025 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import pytest

from apps.chords.constants import (
    MAX_FINGER,
    MAX_FRET,
    MAX_STRING_NUMBER,
    MIN_FINGER,
    MIN_FRET,
    MIN_STRING_NUMBER,
)


@pytest.mark.parametrize(
    "constant, expected_value",
    [
        (MIN_STRING_NUMBER, 1),
        (MAX_STRING_NUMBER, 6),
        (MIN_FRET, -1),
        (MAX_FRET, 12),
        (MIN_FINGER, 0),
        (MAX_FINGER, 4),
    ],
)
def test_guitar_constants(constant: int, expected_value: int) -> None:
    assert constant == expected_value, f"Constant should be {expected_value}"
