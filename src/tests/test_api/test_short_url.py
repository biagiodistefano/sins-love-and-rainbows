import json

import pytest
from django.test.client import Client


@pytest.mark.django_db
def test_short_url(api_client: Client) -> None:
    response = api_client.post(
        "/api/s/create", json.dumps({"url": "https://www.biagiodistefano.io"}), content_type="application/json"
    )
    assert response.status_code == 201
    assert response.json()["url"] == "https://www.biagiodistefano.io"
    assert response.json()["short_url"] is not None

    response = api_client.post(
        "/api/s/create",
        json.dumps({"url": "https://www.biagiodistefano.io", "short_url": "bd"}),
        content_type="application/json",
    )
    assert response.status_code == 201
    assert response.json()["short_url"] == "bd"

    response = api_client.get("/api/s/bd")
    assert response.status_code == 200
    assert response.json()["short_url"] == "bd"

    response = api_client.get("/api/s/")
    assert response.status_code == 200
    assert len(response.json()) == 2

    response = api_client.put(
        "/api/s/bd",
        json.dumps({"url": "https://www.biagiodistefano.io", "short_url": "bd2"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json()["short_url"] == "bd2"

    response = api_client.put(
        "/api/s/bd2", json.dumps({"url": "https://www.biagiodistefano.io/bd2"}), content_type="application/json"
    )
    assert response.status_code == 200
    assert response.json()["short_url"] == "bd2"
    assert response.json()["url"] == "https://www.biagiodistefano.io/bd2"

    response = api_client.delete("/api/s/bd2")
    assert response.status_code == 204
    response = api_client.get("/s/bd2")
    print(response.content)
    assert response.status_code == 404
