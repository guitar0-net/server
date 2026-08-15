# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Services for the schemes app."""

from django.db import transaction
from django.db.models import QuerySet
from PIL import Image as PilImage

from apps.lessons.services import touch_lessons_for_schemes

from .models import ImageScheme
from .selectors import get_all_image_schemes, get_image_scheme_sync_state


class ImageSchemeService:
    """Business logic for the ImageScheme entity."""

    @staticmethod
    @transaction.atomic
    def save_image_scheme(*, scheme: ImageScheme) -> None:
        """Persist a scheme and propagate an observable change to related lessons.

        Every single-row ImageScheme mutation must go through this method —
        calling scheme.save() directly bypasses the propagation and leaves
        Lesson.updated_at stale, so replacing an image stays invisible to
        delta sync and to any cached print output.

        The stored state is compared across the save rather than before it:
        the uploaded file only gets its final name, width and height once
        saved. Editing `code` alone changes nothing a client can see, and
        stamping for it would cost every client a full re-download.
        """
        before = (
            get_image_scheme_sync_state(scheme.pk) if scheme.pk is not None else None
        )
        scheme.save()
        if before != get_image_scheme_sync_state(scheme.pk):
            touch_lessons_for_schemes([scheme.pk])

    @staticmethod
    @transaction.atomic
    def delete_image_scheme(*, scheme: ImageScheme) -> None:
        """Delete a scheme, propagating to related lessons first.

        The song-to-scheme rows that identify the affected lessons are removed
        along with the scheme, so they must be read before the delete.
        """
        if scheme.pk is not None:
            touch_lessons_for_schemes([scheme.pk])
            scheme.delete()

    @staticmethod
    @transaction.atomic
    def delete_image_schemes(*, schemes: QuerySet[ImageScheme]) -> None:
        """Delete every scheme in the queryset, propagating to related lessons.

        Serves the admin bulk action, which never routes through
        `delete_image_scheme`.
        """
        touch_lessons_for_schemes(list(schemes.values_list("pk", flat=True)))
        schemes.delete()

    @staticmethod
    def bulk_recalculate_dimensions() -> int:
        """Read every image file from disk and update width/height in the DB.

        Only schemes whose stored dimensions disagree with the file are written
        and propagated. The command is normally re-run over unchanged files, and
        stamping every lesson regardless would move the whole catalogue past
        `since`, turning each delta sync into a full download.

        Reading the files runs outside the transaction; only the write and the
        propagation share one. They have to, because that skip-unchanged rule
        makes a half-applied run unrepairable: committing the dimensions
        without the stamps leaves a re-run seeing the DB already agreeing with
        the file, finding nothing to change, and never propagating at all.
        Decoding carries no such constraint, and holding the transaction open
        across every image on disk would lock the rows for the whole run.

        Returns:
            int: Number of updated records.
        """
        # Read raw columns rather than loading instances: ImageField's
        # update_dimension_fields runs on post_init and silently replaces a
        # falsy width/height with the real file size, so scheme.width already
        # equals the file for exactly the rows that need writing. Only a raw
        # column read shows what is actually persisted — and it keeps this to
        # one query, with instances built solely for the rows that changed.
        storage = ImageScheme.image.field.storage
        stored = get_all_image_schemes().values_list("pk", "image", "width", "height")

        changed = []
        for pk, image_name, width, height in stored:
            with PilImage.open(storage.path(image_name)) as img:
                actual_width, actual_height = img.size
            if (width, height) == (actual_width, actual_height):
                continue
            # Safe to build without the image: update_dimension_fields returns
            # early on an unset file, so it leaves these dimensions alone, and
            # bulk_update writes none of the omitted columns.
            changed.append(ImageScheme(pk=pk, width=actual_width, height=actual_height))

        with transaction.atomic():
            ImageScheme.objects.bulk_update(changed, ["width", "height"])
            touch_lessons_for_schemes([scheme.pk for scheme in changed])
        return len(changed)
