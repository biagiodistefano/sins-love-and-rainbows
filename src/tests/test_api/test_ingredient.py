import json

import pytest
from django.test.client import Client


@pytest.mark.django_db
def test_ingredient(api_client: Client) -> None:
    create = api_client.post(
        "/api/ingredient/create",
        data=json.dumps({"name": "Tomato"}),
        content_type="application/json",
    )
    assert create.status_code == 201
    ingredient = create.json()
    assert ingredient["name"] == "tomato"
    ingredient_id = ingredient["id"]

    read = api_client.get(f"/api/ingredient/{ingredient_id}")
    assert read.status_code == 200
    assert read.json() == ingredient

    update = api_client.put(
        f"/api/ingredient/{ingredient_id}",
        data=json.dumps({"name": "Potato"}),
        content_type="application/json",
    )
    assert update.status_code == 200
    ingredient = update.json()
    assert ingredient["name"] == "potato"
    read = api_client.get(f"/api/ingredient/{ingredient_id}")
    assert read.status_code == 200
    assert read.json() == ingredient

    ingredient_2 = api_client.post(
        "/api/ingredient/create",
        data=json.dumps({"name": "Banana"}),
        content_type="application/json",
    )
    assert ingredient_2.status_code == 201

    ingredient_list = api_client.get("/api/ingredient/all")
    assert ingredient_list.status_code == 200
    assert len(ingredient_list.json()) == 2
    assert set(i["name"] for i in ingredient_list.json()) == {"potato", "banana"}

    delete = api_client.delete(f"/api/ingredient/{ingredient_id}")
    assert delete.status_code == 204
    read = api_client.get(f"/api/ingredient/{ingredient_id}")
    assert read.status_code == 404

    ingredient_list = api_client.get("/api/ingredient/all")
    assert ingredient_list.status_code == 200
    assert len(ingredient_list.json()) == 1
    assert set(i["name"] for i in ingredient_list.json()) == {"banana"}
