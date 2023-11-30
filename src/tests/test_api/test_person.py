import json

import pytest
from django.test.client import Client


@pytest.mark.django_db
def test_person(api_client: Client) -> None:
    create = api_client.post(
        "/api/person/create",
        data=json.dumps({"name": "John Doe", "from_abroad": False, "in_broadcast": True}),
        content_type="application/json",
    )
    assert create.status_code == 201
    person = create.json()
    person_id = person["id"]

    read = api_client.get("/api/person/" + person_id)
    assert read.status_code == 200
    assert read.json() == person

    update = api_client.put(
        "/api/person/" + person_id,
        data=json.dumps({"name": "Jane Doe", "from_abroad": True, "in_broadcast": False}),
        content_type="application/json",
    )
    assert update.status_code == 200
    person = update.json()
    read = api_client.get("/api/person/" + person_id)
    assert read.status_code == 200
    assert read.json() == person

    delete = api_client.delete("/api/person/" + person_id)
    assert delete.status_code == 204
    read = api_client.get("/api/person/" + person_id)
    assert read.status_code == 404
