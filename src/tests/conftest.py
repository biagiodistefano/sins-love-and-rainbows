import json

import pytest
from django.test.client import Client
from api.models import ApiClient


@pytest.fixture
@pytest.mark.django_db
def api_client():
    api_client_instance = ApiClient.objects.create(name="test_client")
    auth_client = Client(HTTP_X_API_KEY=api_client_instance.api_key)
    return auth_client
