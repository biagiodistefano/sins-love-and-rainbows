from django.conf import settings

API_VERSION = "v0.0.1"
USE_AUTH = getattr(settings, "SLR_USE_AUTH", True)
