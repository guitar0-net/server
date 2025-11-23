# SPDX-FileCopyrightText: 2025 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later


"""Factory for generating test User instances.

This factory uses factory-boy and faker to create realistic User objects
for testing, ensuring isolation and repeatability across test cases.
"""

import factory
from factory.django import DjangoModelFactory
from faker import Faker

from apps.accounts.models.user import User

fake = Faker()


class UserFactory(DjangoModelFactory[User]):
    """Factory for creating User instances with default realistic data.

    This factory generates users with email as primary identifier,
    integrating with UserManager for proper password handling.
    It supports overriding fields for specific test scenarios.

    Attributes:
        email: Generated unique email.
        password: Hashed password (set via post-generation).
    """

    class Meta:
        """Metadata for UserFactory."""

        model = User
        skip_postgeneration_save = True

    email = fake.email()

    @factory.post_generation  # type: ignore[misc, attr-defined]
    def password(
        self, create: bool, extracted: str | None, **kwargs: dict[str, str]
    ) -> None:
        """Post-generation hook to set password properly."""
        if create:
            self.set_password(extracted or fake.password())  # type: ignore[attr-defined]
            self.save()  # type: ignore[attr-defined]
