from .base import DEBUG
from decouple import config


EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="me@biagiodistefano.io")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="password")
EMAIL_USE_SSL = config("EMAIL_USE_SSL", cast=bool, default=True)
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="me@biagiodistefano.io")
if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
ADMINS = [("Biagio", "me+slr@biagiodistefano.io")]
