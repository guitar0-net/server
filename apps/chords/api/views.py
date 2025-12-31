# SPDX-FileCopyrightText: 2025 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Views for the chords app."""

from typing import Any, TypedDict, Unpack, cast

from django.db.models import QuerySet
from django.http import Http404
from rest_framework import status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from apps.shared.permissions import IsStaffOrReadOnly

from ..models import Chord
from ..selectors import get_all_chords, get_full_chord_by_id
from ..services import ChordCreateDict, ChordService
from .serializers import ChordCreateUpdateSerializer, ChordOutputSerializer


class ChordViewSetKwargs(TypedDict):
    """Type for kwargs argument."""

    pk: str


class ChordViewSet(viewsets.ModelViewSet[Chord]):
    """ViewSet for CRUD operations on Chord model."""

    permission_classes = (IsStaffOrReadOnly,)

    def get_queryset(self) -> QuerySet[Chord]:  # noqa: PLR6301
        """Get the queryset of all chords.

        Returns:
            QuerySet[Chord]: QuerySet of all chords
        """
        return get_all_chords()

    def get_object(self) -> Chord:
        """Get a single chord instance with full related data.

        Returns:
            Chord: The chord instance with prefetched relations

        Raises:
            Http404: If chord is not found
        """
        pk = self.kwargs["pk"]
        try:
            return get_full_chord_by_id(chord_id=int(pk))
        except Chord.DoesNotExist as e:
            raise Http404("Chord not found.") from e

    def get_serializer_class(self) -> type[Serializer[Any]]:
        """Return serializer class based on action.

        Returns:
            Serializer class for the current action
        """
        if self.action in {"create", "update", "partial_update"}:
            return ChordCreateUpdateSerializer
        return ChordOutputSerializer

    def create(self, request: Request) -> Response:
        """Create a new chord (admin only).

        Args:
            request: The incoming request with chord data

        Returns:
            Response with created chord or validation errors
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        positions = serializer.validated_data["positions"]
        chord_fields = cast(
            ChordCreateDict,
            {k: v for k, v in serializer.validated_data.items() if k != "positions"},
        )

        chord = ChordService.create_chord(
            positions=positions,
            chord_fields=chord_fields,
        )

        output_serializer = ChordOutputSerializer(chord)
        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    def update(
        self,
        request: Request,
        **kwargs: Unpack[ChordViewSetKwargs],
    ) -> Response:
        """Fully update a chord (admin only).

        Args:
            request (Request): The incoming request with chord data
            **kwargs (Any): Additional keyword arguments passed by DRF dispatch,
                including 'pk' used to identify the chord instance.

        Returns:
            Response with updated chord or errors
        """
        return self._perform_update(request, partial=False)

    def partial_update(
        self,
        request: Request,
        **kwargs: Unpack[ChordViewSetKwargs],
    ) -> Response:
        """Update a chord partially (admin only).

        Args:
            request (Request): The incoming request with partial chord data
            **kwargs (Any): Additional keyword arguments passed by DRF dispatch,
                including 'pk' used to identify the chord instance.

        Returns:
            Response with updated chord or errors
        """
        return self._perform_update(request, partial=True)

    def destroy(
        self, request: Request, **kwargs: Unpack[ChordViewSetKwargs]
    ) -> Response:
        """Delete a chord (admin only).

        Args:
            request (Request): The incoming request
            **kwargs (Any): Additional keyword arguments passed by DRF dispatch,
                including 'pk' used to identify the chord instance.

        Returns:
            Response with 204 No Content or 404 if not found
        """
        chord = self.get_object()
        ChordService.delete_chord(chord=chord)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _perform_update(self, request: Request, partial: bool = False) -> Response:
        """Perform update operation (full or partial).

        Args:
            request: The incoming request with chord data
            partial: Whether to perform partial update

        Returns:
            Response with updated chord or errors
        """
        chord = self.get_object()
        serializer = self.get_serializer(chord, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        updated_chord = ChordService.update_chord(
            chord=chord,
            data=serializer.validated_data,
        )

        output_serializer = ChordOutputSerializer(updated_chord)
        return Response(output_serializer.data)
