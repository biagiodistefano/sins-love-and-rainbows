from decouple import config

TWILIO_ACCOUNT_SID = config("TWILIO_ACCOUNT_SID", default=None)
TWILIO_AUTH_TOKEN = config("TWILIO_AUTH_TOKEN", default=None)
TWILIO_FROM_WHATSAPP_NUMBER = config("TWILIO_FROM_WHATSAPP_NUMBER", default=None)

DEBUG_NUMBERS_ALLOWED = config("DEBUG_NUMBERS_ALLOWED", cast=lambda v: [s.strip() for s in v.split(",")], default="")
MY_PHONE_NUMBER = config("MY_PHONE_NUMBER", default=None)
NGROK_URL = config("NGROK_URL", default=None)
