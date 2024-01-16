import json

import pytest
from django.test.client import Client


@pytest.mark.django_db
def test_external_link(api_client: Client) -> None:
    create = api_client.post(
        "/api/party/create",
        data=json.dumps(
            {
                "name": "Test Party",
                "edition": "test-party",
                "date_and_time": "2021-08-17T18:00:00Z",
                "location": "Test Location",
                "description": "Test Description",
            }
        ),
        content_type="application/json",
    )
    assert create.status_code == 201
    party = create.json()
    party_edition = party["edition"]

    assert party["externallink_set"] == []

    create = api_client.post(
        f"/api/party/{party_edition}/external-link/create",
        data=json.dumps(
            {"name": "Party Playlist", "url": "https://www.playlist.com/random", "description": "Test Playlist"}
        ),
        content_type="application/json",
    )
    assert create.status_code == 201
    external_link = create.json()
    external_link_id = external_link["id"]

    read = api_client.get(f"/api/party/{party_edition}")
    assert read.status_code == 200
    assert len(read.json()["externallink_set"]) == 1

    read = api_client.get(f"/api/party/{party_edition}/external-link/{external_link_id}")
    assert read.status_code == 200
    assert read.json() == external_link

    update = api_client.put(
        f"/api/party/{party_edition}/external-link/{external_link_id}",
        data=json.dumps({"description": "Test Playlist 2"}),
        content_type="application/json",
    )
    assert update.status_code == 200
    read = api_client.get(f"/api/party/{party_edition}/external-link/{external_link_id}")
    assert read.status_code == 200
    assert read.json()["description"] == "Test Playlist 2"

    create = api_client.post(
        f"/api/party/{party_edition}/external-link/create",
        data=json.dumps(
            {"name": "Party Playlist 2", "url": "https://www.playlist.com/random2", "description": "Test Playlist 3"}
        ),
        content_type="application/json",
    )
    assert create.status_code == 201

    read = api_client.get(f"/api/party/{party_edition}/external-link/all")
    assert read.status_code == 200
    assert len(read.json()) == 2
    assert set(m["name"] for m in read.json()) == {"Party Playlist", "Party Playlist 2"}

    delete = api_client.delete(f"/api/party/{party_edition}/external-link/{external_link_id}")
    assert delete.status_code == 204
    read = api_client.get(f"/api/party/{party_edition}/external-link/{external_link_id}")
    assert read.status_code == 404
    read = api_client.get(f"/api/party/{party_edition}/external-link/all")
    assert read.status_code == 200
    assert len(read.json()) == 1
    assert read.json()[0]["description"] == "Test Playlist 3"

    delete = api_client.delete(f"/api/party/{party_edition}/external-link/all")
    assert delete.status_code == 204
    read = api_client.get(f"/api/party/{party_edition}/external-link/all")
    assert read.status_code == 200
    assert len(read.json()) == 0
