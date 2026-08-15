# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Selectors for the schemes app."""

from typing import Final

from django.db.models import QuerySet

from .models import ImageScheme

SYNC_FIELDS: Final[tuple[str, ...]] = ("image", "inscription", "height", "width")
"""Scheme fields the sync payload exposes — must mirror `SchemeSyncSerializer`.

`code` is deliberately absent: it is an internal label no client ever sees, so
renaming one must not stamp every related lesson. Public because the mirroring
is the contract, not an implementation detail —
`test_image_scheme_sync_state_covers_every_serialized_field` fails the build if
a field is added to the serializer without being added here. Without that guard
the drift is silent: an edit to the new field would be read as "nothing
changed" and never reach a delta-sync client.
"""


def get_image_scheme_sync_state(scheme_id: int) -> tuple[object, ...] | None:
    """Get the persisted values of every scheme field the sync payload exposes.

    Services compare the state read before a write with the one read after it,
    so that a change clients cannot observe does not stamp every related lesson
    and force a full re-download.

    Returns:
        tuple[object, ...] | None: Field values in declaration order, or None
            if no such scheme exists.
    """
    return ImageScheme.objects.filter(pk=scheme_id).values_list(*SYNC_FIELDS).first()


def get_all_image_schemes() -> QuerySet[ImageScheme]:
    """Get a QuerySet of all ImageScheme objects.

    Returns:
        QuerySet[ImageScheme]: All image schemes.
    """
    return ImageScheme.objects.all()
