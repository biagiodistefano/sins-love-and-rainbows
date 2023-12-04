import json

import pytest
from django.test.client import Client


@pytest.mark.django_db
def test_allergy(api_client: Client) -> None:
    ingredient_ids = []
    for name in ["Potato", "Tomato", "Egg"]:
        create = api_client.post(
            "/api/ingredient/create",
            data=json.dumps({"name": name}),
            content_type="application/json",
        )
        assert create.status_code == 201
        ingredient_ids.append(create.json()["id"])

    random_ingredient_ids = []
    for random_ingredient in ["Pasta", "Rice", "Bread"]:
        create = api_client.post(
            "/api/ingredient/create",
            data=json.dumps({"name": random_ingredient}),
            content_type="application/json",
        )
        assert create.status_code == 201
        random_ingredient_ids.append(create.json()["id"])

    allergic_people_ids = []
    for name in ["Tizio", "Caio", "Sempronio"]:
        create = api_client.post(
            "/api/person/create",
            data=json.dumps({"username": name, "first_name": name, "from_abroad": False, "in_broadcast": True}),
            content_type="application/json",
        )
        assert create.status_code == 201
        allergic_people_ids.append(create.json()["id"])

    random_people_ids = []
    for random_person in ["Giovanni", "Marco", "Luca"]:
        create = api_client.post(
            "/api/person/create",
            data=json.dumps(
                {"username": random_person, "first_name": random_person, "from_abroad": False, "in_broadcast": True}
                ),
            content_type="application/json",
        )
        assert create.status_code == 201
        random_people_ids.append(create.json()["id"])

    for person_id in allergic_people_ids:
        for ingredient_id in ingredient_ids:
            create = api_client.post(
                f"/api/ingredient/{ingredient_id}/allergy/{person_id}/create",
            )
            assert create.status_code == 201

    for ingredient_id in ingredient_ids:
        read = api_client.get(f"/api/ingredient/{ingredient_id}/allergy")
        assert read.status_code == 200
        assert set(p["id"] for p in read.json()) == set(allergic_people_ids)

    for person_id in allergic_people_ids:
        read = api_client.get(f"/api/person/{person_id}/allergies")
        assert read.status_code == 200
        assert set(i["id"] for i in read.json()) == set(ingredient_ids)

    ingredient_id = ingredient_ids[0]
    person_id = allergic_people_ids[0]

    delete_allergy = api_client.delete(f"/api/ingredient/{ingredient_id}/allergy/{person_id}")
    assert delete_allergy.status_code == 204
    read = api_client.get(f"/api/ingredient/{ingredient_id}/allergy")
    assert read.status_code == 200
    assert set(p["id"] for p in read.json()) == set(allergic_people_ids[1:])

    for person_id in random_people_ids:
        read = api_client.get(f"/api/person/{person_id}/allergies")
        assert read.status_code == 200
        assert read.json() == []
