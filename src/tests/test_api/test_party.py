import json

import pytest
from django.test.client import Client
from api.models import Person


@pytest.mark.django_db
def test_party(api_client: Client) -> None:
    Person.objects.all().delete()
    for name in ["Tizio", "Caio", "Sempronio"]:
        create = api_client.post(
            "/api/person/create",
            data=json.dumps({"username": name, "first_name": "name", "from_abroad": False, "in_broadcast": True}),
            content_type="application/json",
        )
        assert create.status_code == 201

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

    assert party["invite_summary"] == {"yes": 0, "maybe": 0, "no": 0, "no_response": 3, "from_abroad": 0}
    assert len(party["invite_set"]) == 3

    party_edition = party["edition"]

    read = api_client.get("/api/party/" + party_edition)
    assert read.status_code == 200
    assert read.json() == party

    update = api_client.put(
        "/api/party/" + party_edition,
        data=json.dumps(
            {
                "name": "Test Party 2",
                "edition": "test-party-2",
                "date_and_time": "2021-08-17T18:00:00Z",
                "location": "Test Location 2",
                "description": "Test Description 2",
            }
        ),
        content_type="application/json",
    )
    assert update.status_code == 200
    party = update.json()
    party_edition = party["edition"]
    read = api_client.get("/api/party/" + party_edition)
    assert read.status_code == 200
    assert read.json() == party

    delete = api_client.delete("/api/party/" + party_edition)
    assert delete.status_code == 204
    read = api_client.get("/api/party/" + party_edition)
    assert read.status_code == 404


@pytest.mark.django_db
def test_party_invite(api_client: Client) -> None:
    Person.objects.all().delete()
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

    assert party["invite_summary"] == {"yes": 0, "maybe": 0, "no": 0, "no_response": 0, "from_abroad": 0}
    assert len(party["invite_set"]) == 0

    people_ids = []
    for name in ["Tizio", "Caio", "Sempronio"]:
        create = api_client.post(
            "/api/person/create",
            data=json.dumps({"username": name, "first_name": "name", "from_abroad": False, "in_broadcast": True}),
            content_type="application/json",
        )
        assert create.status_code == 201
        people_ids.append(create.json()["id"])

    for person_id in people_ids:
        create = api_client.post(
            f"/api/party/{party_edition}/invite/{person_id}/create",
        )
        assert create.status_code == 201

    read = api_client.get("/api/party/" + party_edition)
    assert read.status_code == 200
    party = read.json()
    assert party["invite_summary"] == {"yes": 0, "maybe": 0, "no": 0, "no_response": 3, "from_abroad": 0}
    assert len(party["invite_set"]) == 3

    party_invites = api_client.get(f"/api/party/{party_edition}/invite/all")
    assert party_invites.status_code == 200
    assert party_invites.json() == party["invite_set"]

    not_invited_people = api_client.get(f"/api/party/{party_edition}/not-invited/all")
    assert not_invited_people.status_code == 200
    assert not_invited_people.json() == party["not_invited_people"]

    person_0_id, person_1_id, person_2_id = people_ids

    update = api_client.put(f"/api/party/{party_edition}/invite/{person_0_id}/y")
    assert update.status_code == 200
    update = api_client.put(f"/api/party/{party_edition}/invite/{person_1_id}/m")
    assert update.status_code == 200
    update = api_client.put(f"/api/party/{party_edition}/invite/{person_2_id}/n")
    assert update.status_code == 200

    api_client.put("/api/person/" + person_0_id, data=json.dumps({"from_abroad": True}))

    read = api_client.get("/api/party/" + party_edition)
    assert read.status_code == 200
    party = read.json()
    assert party["invite_summary"] == {"yes": 1, "maybe": 1, "no": 1, "no_response": 0, "from_abroad": 1}

    delete = api_client.delete(f"/api/party/{party_edition}/invite/{person_0_id}")
    assert delete.status_code == 204
    read = api_client.get("/api/party/" + party_edition)
    assert read.status_code == 200
    party = read.json()
    assert party["invite_summary"] == {"yes": 0, "maybe": 1, "no": 1, "no_response": 0, "from_abroad": 0}

    update = api_client.put(f"/api/party/{party_edition}/invite/{person_0_id}/y")
    assert update.status_code == 200
    read = api_client.get("/api/party/" + party_edition)
    assert read.status_code == 200
    party = read.json()
    assert party["invite_summary"] == {"yes": 1, "maybe": 1, "no": 1, "no_response": 0, "from_abroad": 1}

    create = api_client.post(
        "/api/ingredient/create", data=json.dumps({"name": "Tomato"}), content_type="application/json"
    )
    assert create.status_code == 201
    ingredient_id = create.json()["id"]
    create = api_client.post(
        f"/api/ingredient/{ingredient_id}/allergy/{person_0_id}/create",
    )
    assert create.status_code == 201
    read = api_client.get("/api/party/" + party_edition)
    assert read.status_code == 200
    party = read.json()
    assert party["allergy_list"] == ["tomato"]

    update = api_client.put(f"/api/party/{party_edition}/invite/{person_0_id}/n")
    assert update.status_code == 200
    read = api_client.get("/api/party/" + party_edition)
    assert read.status_code == 200
    party = read.json()
    assert party["allergy_list"] == []


@pytest.mark.django_db
def test_party_list(api_client: Client) -> None:
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

    read = api_client.get("/api/party/all")
    assert read.status_code == 200
    assert len(read.json()) == 1
    assert read.json()[0]["edition"] == party_edition

    delete = api_client.delete("/api/party/" + party_edition)
    assert delete.status_code == 204

    read = api_client.get("/api/party/all")
    assert read.status_code == 200
    assert read.json() == []
