# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Pytest fixtures for testing schemes app."""

import pytest

from apps.schemes.models import ImageScheme
from apps.schemes.tests.factories import ImageSchemeFactory


@pytest.fixture
def image_scheme_factory() -> type[ImageSchemeFactory]:
    """Fixture providing the ImageSchemeFactory for creating image schemes in tests."""
    return ImageSchemeFactory


@pytest.fixture
def image_scheme() -> ImageScheme:
    """Fixture creating an image scheme for testing.

    Returns:
        ImageScheme: scheme instance
    """
    return ImageSchemeFactory.create()
