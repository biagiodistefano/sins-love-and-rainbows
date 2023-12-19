from django.http import HttpRequest
from ninja.constants import NOT_SET
from ninja.security import APIKeyHeader  # , django_auth
# from ninja_jwt.authentication import JWTAuth

from api.models import ApiClient
from .settings import USE_AUTH
from django.conf import settings
from twilio.request_validator import RequestValidator



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


class TwilioAuth(APIKeyHeader):
    param_name = "X-Twilio-Signature"

    def authenticate(self, request: HttpRequest, key: str):
        try:
            validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)

            # The URL that Twilio POSTed to
            url = request.build_absolute_uri()

            # The POST variables Twilio sent with the request
            post_vars = request.POST.dict()
            # The Twilio signature from the X-Twilio-Signature header
            return validator.validate(url, post_vars, key)
        except Exception as e:
            pass
