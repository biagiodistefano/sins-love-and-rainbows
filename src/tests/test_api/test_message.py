import json

import pytest
from django.test.client import Client


@pytest.mark.django_db
def test_message(api_client: Client) -> None:
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

    assert len(party["message_set"]) == 4

    create = api_client.post(
        f"/api/party/{party_edition}/message/create",
        data=json.dumps({"text": "Test Message"}),
        content_type="application/json",
    )
    assert create.status_code == 201
    message = create.json()
    message_id = message["id"]

    read = api_client.get(f"/api/party/{party_edition}")
    assert read.status_code == 200
    assert len(read.json()["message_set"]) == 5

    read = api_client.get(f"/api/party/{party_edition}/message/{message_id}")
    assert read.status_code == 200
    assert read.json() == message

    update = api_client.put(
        f"/api/party/{party_edition}/message/{message_id}",
        data=json.dumps({"text": "Test Message 2"}),
        content_type="application/json",
    )
    assert update.status_code == 200
    read = api_client.get(f"/api/party/{party_edition}/message/{message_id}")
    assert read.status_code == 200
    assert read.json()["text"] == "Test Message 2"

    # create = api_client.post(
    #     f"/api/party/{party_edition}/message/create",
    #     data=json.dumps({"text": "Test Message 3"}),
    #     content_type="application/json",
    # )
    # assert create.status_code == 201
    # to_send_message = create.json()
    # to_send_message_id = to_send_message["id"]

    # send = api_client.post(
    #     f"/api/party/{party_edition}/message/{to_send_message_id}/send",
    # )
    # assert send.status_code == 202

    send_404 = api_client.post(
        f"/api/party/{party_edition}/message/17/send",
    )
    assert send_404.status_code == 404

    read = api_client.get(f"/api/party/{party_edition}/message/all")
    assert read.status_code == 200
    assert len(read.json()) == 5

    delete = api_client.delete(f"/api/party/{party_edition}/message/{message_id}")
    assert delete.status_code == 204
    read = api_client.get(f"/api/party/{party_edition}/message/{message_id}")
    assert read.status_code == 404
    read = api_client.get(f"/api/party/{party_edition}/message/all")
    assert read.status_code == 200
    assert len(read.json()) == 4

    delete = api_client.delete(f"/api/party/{party_edition}/message/all")
    assert delete.status_code == 204
    read = api_client.get(f"/api/party/{party_edition}/message/all")
    assert read.status_code == 200
    assert len(read.json()) == 0
