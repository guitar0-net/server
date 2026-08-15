# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Views for the sync app."""

import logging
from datetime import UTC, datetime
from typing import Any

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.chords.models import Chord
from apps.lessons.models import Lesson
from apps.schemes.models import ImageScheme
from apps.sync.selectors import (
    get_content_version,
    get_course_lessons_for_sync,
    get_courses_for_sync,
    get_lessons_for_sync,
    get_published_course_uuids,
    get_published_lesson_uuids,
)

from .serializers.sync_serializers import (
    ContentVersionResponseSerializer,
    SyncLessonsResponseSerializer,
)

logger = logging.getLogger("sync")

_SINCE_PARAM = OpenApiParameter(
    name="since",
    type=str,
    location=OpenApiParameter.QUERY,
    description=(
        "ISO-8601 timestamp. When provided, only lessons updated after this "
        "point are included in `lessons`, `songs`, `chords`, and `schemes`. "
        "`lesson_uuids` always contains the full set of published UUIDs "
        "regardless of this parameter."
    ),
    required=False,
    examples=[],
)


@extend_schema(
    parameters=[_SINCE_PARAM], responses={200: SyncLessonsResponseSerializer}
)
class LessonsSyncView(APIView):
    """Flat sync payload for offline download.

    Returns a normalized response where each entity type is in its own
    top-level array (no nesting). Songs reference chords and schemes by ID.

    Delta sync: use `?since=<ISO-8601>` to receive only changed lessons and
    their associated songs/chords/schemes. `lesson_uuids` and `course_*`
    fields are always the complete published set regardless of `since`.
    """

    permission_classes = (AllowAny,)

    def get(self, request: Request) -> Response:
        """Return flat sync payload."""
        since = self._parse_since(request)
        if since is None and "since" in request.query_params:
            return Response(
                {"detail": "Invalid `since` value — expected ISO-8601 datetime."},
                status=400,
            )

        # Read the version before the lessons, never after. A concurrent touch
        # landing between the two queries would otherwise be reflected in the
        # version but absent from the payload, and the client — which stores
        # the version as its next `since` — would skip that change forever.
        # Reading first can only cost a redundant re-sync.
        version = get_content_version()
        lessons_list = list(get_lessons_for_sync(since))
        songs_out, chord_map, scheme_map = self._collect_song_data(lessons_list)

        logger.debug(
            "Sync: since=%s lessons=%d songs=%d chords=%d schemes=%d",
            since,
            len(lessons_list),
            len(songs_out),
            len(chord_map),
            len(scheme_map),
        )

        payload = {
            "version": version,
            "lesson_uuids": get_published_lesson_uuids(),
            "lessons": lessons_list,
            "songs": songs_out,
            "chords": list(chord_map.values()),
            "schemes": list(scheme_map.values()),
            "course_uuids": get_published_course_uuids(),
            "courses": get_courses_for_sync(),
            "course_lessons": get_course_lessons_for_sync(),
        }
        return Response(SyncLessonsResponseSerializer(payload).data)

    @staticmethod
    def _collect_song_data(
        lessons: list[Lesson],
    ) -> tuple[list[dict[str, Any]], dict[int, Chord], dict[int, ImageScheme]]:
        """Collect songs, chords, and schemes from prefetched lessons.

        No extra DB queries. A song shared across multiple lessons appears once
        per lesson with a different lesson_uuid — mirrors the M2M relationship.
        """
        songs_out: list[dict[str, Any]] = []
        chord_map: dict[int, Chord] = {}
        scheme_map: dict[int, ImageScheme] = {}

        for lesson in lessons:
            for song in lesson.songs.all():
                song_chords = list(song.chords.all())
                song_schemes = list(song.schemes.all())
                songs_out.append({
                    "uuid": song.uuid,
                    "lesson_uuid": lesson.uuid,
                    "title": song.title,
                    "text": song.text,
                    "metronome": song.metronome,
                    "chord_ids": [c.pk for c in song_chords],
                    "scheme_ids": [s.pk for s in song_schemes],
                })
                for c in song_chords:
                    chord_map.setdefault(c.pk, c)
                for s in song_schemes:
                    scheme_map.setdefault(s.pk, s)

        return songs_out, chord_map, scheme_map

    @staticmethod
    def _parse_since(request: Request) -> datetime | None:
        """Parse the ?since= query param.

        Returns None if the param is absent (not an error).
        Returns None if the param is present but invalid (caller checks
        `"since" in request.query_params` to distinguish the two cases).
        """
        raw = request.query_params.get("since")
        if raw is None:
            return None
        try:
            dt = datetime.fromisoformat(raw)
        except ValueError:
            return None
        else:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            return dt


@extend_schema(responses={200: ContentVersionResponseSerializer})
class ContentVersionView(APIView):
    """Lightweight endpoint for staleness checks.

    The client calls this on app launch. If `version` matches the locally
    stored value, no sync is needed. Only when it differs does the client
    call `LessonsSyncView`.
    """

    permission_classes = (AllowAny,)

    def get(self, request: Request) -> Response:  # noqa: PLR6301
        """Return current content version."""
        payload = {"version": get_content_version()}
        return Response(ContentVersionResponseSerializer(payload).data)
