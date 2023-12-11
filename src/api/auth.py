from django.http import HttpRequest
from ninja.constants import NOT_SET
from ninja.security import APIKeyHeader  # , django_auth
# from ninja_jwt.authentication import JWTAuth

from api.models import ApiClient
from .settings import USE_AUTH


class ApiKey(APIKeyHeader):
    param_name = "X-API-Key"

    def authenticate(self, request: HttpRequest, key: str):
        try:
            return ApiClient.objects.get(api_key=key, active=True)
        except ApiClient.DoesNotExist:
            pass


if USE_AUTH:
    AUTH = [ApiKey()]  # , JWTAuth(), django_auth]
else:
    AUTH = NOT_SET
