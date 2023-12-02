import json

import pytest
from django.contrib.auth import get_user_model
from django.test.client import Client

User = get_user_model()


@pytest.fixture
@pytest.mark.django_db
def api_client():
    User.objects.create_user(username='test_user', password='test-password')
    client = Client()
    resp = client.post(
        "/api/token/pair",
        data=json.dumps({"username": "test_user", "password": "test-password"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    token = resp.json()["access"]
    auth_client = Client(HTTP_AUTHORIZATION=f'Bearer {token}')
    return auth_client
