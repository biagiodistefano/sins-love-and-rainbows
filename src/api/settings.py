from django.conf import settings

USE_AUTH = getattr(settings, "SLR_USE_AUTH", True)
DEBUG = getattr(settings, "DEBUG", False)
TWILIO_ACCOUNT_SID = getattr(settings, "TWILIO_ACCOUNT_SID", None)
TWILIO_AUTH_TOKEN = getattr(settings, "TWILIO_AUTH_TOKEN", None)
TWILIO_FROM_WHATSAPP_NUMBER = getattr(settings, "TWILIO_FROM_WHATSAPP_NUMBER", None)
DEBUG_NUMBERS_ALLOWED = getattr(settings, "DEBUG_NUMBERS_ALLOWED", [])
NGROK_URL = getattr(settings, "NGROK_URL", None)
MY_PHONE_NUMBER = getattr(settings, "MY_PHONE_NUMBER", None)
