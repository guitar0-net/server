# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later


"""Factory for generating test ImageScheme instances."""

from factory import Faker, Sequence  # type: ignore[attr-defined]
from factory.django import DjangoModelFactory, ImageField

from apps.schemes.models import ImageScheme


class ImageSchemeFactory(DjangoModelFactory[ImageScheme]):
    """Factory for creating ImageScheme instances."""

    code = Sequence(lambda n: f"scheme-{n}")
    inscription = Faker("sentence", nb_words=2)
    image = ImageField(width=800, height=600)

    class Meta:
        model = ImageScheme
