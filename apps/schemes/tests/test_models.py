# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import pytest
from django.db import IntegrityError

from apps.schemes.models import ImageScheme
from apps.schemes.tests.factories import ImageSchemeFactory


@pytest.mark.django_db
def test_code_is_unique(image_scheme_factory: ImageSchemeFactory) -> None:
    image_scheme_factory.create(code="beat-1")
    with pytest.raises(IntegrityError):
        image_scheme_factory.create(code="beat-1")


@pytest.mark.django_db
def test_image_dimensions_are_set_on_save(image_scheme: ImageScheme) -> None:
    scheme = image_scheme

    assert scheme.height is not None
    assert scheme.width is not None
    assert scheme.height > 0
    assert scheme.width > 0
    assert scheme.image.name.startswith("lesson_schemes/")


@pytest.mark.django_db
def test_str_representation(image_scheme_factory: ImageSchemeFactory) -> None:
    scheme = image_scheme_factory.create(code="beat-1", inscription="Бой №1")
    assert str(scheme) == "beat-1: Бой №1"
