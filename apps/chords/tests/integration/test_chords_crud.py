# SPDX-FileCopyrightText: 2025 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Integration tests for chords app."""

from typing import TypedDict

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models.user import User


class ChordPositionData(TypedDict):
    string_number: int
    fret: int
    finger: int


class ChordOutputData(TypedDict):
    id: int
    title: str
    musical_title: str
    order_in_note: int
    start_fret: int
    has_barre: bool
    positions: list[ChordPositionData]


class ChordInputData(TypedDict):
    title: str
    musical_title: str
    order_in_note: int
    start_fret: int
    has_barre: bool
    positions: list[ChordPositionData]


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.fixture
def auth_api_client(client: APIClient, superuser: User) -> APIClient:
    client.force_authenticate(superuser)
    return client


@pytest.mark.integration
@pytest.mark.django_db
def test_chords_full_crud_success_flow(auth_api_client: APIClient) -> None:
    # CREATE
    create_payload: ChordInputData = {
        "title": "Am",
        "musical_title": "A minor",
        "order_in_note": 1,
        "start_fret": 1,
        "has_barre": False,
        "positions": [
            {"string_number": 1, "fret": 0, "finger": 0},
            {"string_number": 2, "fret": 1, "finger": 1},
            {"string_number": 3, "fret": 2, "finger": 3},
            {"string_number": 4, "fret": 2, "finger": 2},
            {"string_number": 5, "fret": 0, "finger": 0},
            {"string_number": 6, "fret": 0, "finger": 0},
        ],
    }

    create_response = auth_api_client.post(
        "/api/v1/data/chords/", create_payload, format="json"
    )
    data: ChordOutputData = create_response.data

    assert create_response.status_code == status.HTTP_201_CREATED
    assert data["title"] == create_payload["title"]
    assert data["musical_title"] == create_payload["musical_title"]
    assert data["order_in_note"] == create_payload["order_in_note"]
    assert data["start_fret"] == create_payload["start_fret"]
    assert data["has_barre"] == create_payload["has_barre"]
    assert len(data["positions"]) == len(create_payload["positions"])

    for pos_input, pos_output in zip(
        create_payload["positions"], data["positions"], strict=False
    ):
        assert pos_input["string_number"] == pos_output["string_number"]
        assert pos_input["fret"] == pos_output["fret"]
        assert pos_input["finger"] == pos_output["finger"]

    # GET
    chord_id = data["id"]
    retrieve_response = auth_api_client.get(f"/api/v1/data/chords/{chord_id}/")
    assert retrieve_response.status_code == status.HTTP_200_OK
    retrieved_data = retrieve_response.json()
    assert retrieved_data == data

    # LIST
    list_response = auth_api_client.get("/api/v1/data/chords/")
    assert list_response.status_code == status.HTTP_200_OK
    assert any(c["id"] == chord_id for c in list_response.json())

    # UPDATE
    update_payload = {
        "title": "Am Updated",
        "musical_title": "A minor updated",
        "order_in_note": 2,
        "start_fret": 1,
        "has_barre": True,
        "positions": [
            {"string_number": 1, "fret": 0, "finger": 0},
            {"string_number": 2, "fret": 1, "finger": 1},
            {"string_number": 3, "fret": 2, "finger": 2},  # changed
            {"string_number": 4, "fret": 2, "finger": 2},
            {"string_number": 5, "fret": 0, "finger": 0},
            {"string_number": 6, "fret": 0, "finger": 0},
        ],
    }

    update_response = auth_api_client.put(
        f"/api/v1/data/chords/{chord_id}/", update_payload, format="json"
    )
    assert update_response.status_code == status.HTTP_200_OK
    updated_data = update_response.json()
    assert updated_data["title"] == "Am Updated"
    assert updated_data["positions"][2]["finger"] == 2

    # PARTIAL UPDATE
    partial_update_payload = {
        "title": "Am Partial",
        "has_barre": False,
    }

    partial_update_response = auth_api_client.patch(
        f"/api/v1/data/chords/{chord_id}/", partial_update_payload, format="json"
    )
    assert partial_update_response.status_code == status.HTTP_200_OK
    partial_updated_data = partial_update_response.json()
    assert partial_updated_data["title"] == "Am Partial"
    assert partial_updated_data["has_barre"] is False
    assert partial_updated_data["musical_title"] == "A minor updated"

    # DELETE
    delete_response = auth_api_client.delete(f"/api/v1/data/chords/{chord_id}/")
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT

    not_found_response = auth_api_client.get(f"/api/v1/data/chords/{chord_id}/")
    assert not_found_response.status_code == status.HTTP_404_NOT_FOUND
