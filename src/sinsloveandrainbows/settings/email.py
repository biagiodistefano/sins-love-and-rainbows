from .base import DEBUG
from decouple import config


EMAIL_HOST = config("EMAIL_HOST")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_HOST_USER = config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
EMAIL_USE_SSL = config("EMAIL_USE_SSL", cast=bool, default=True)
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL")
if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
ADMINS = [("Biagio", "me+slr@biagiodistefano.io")]
