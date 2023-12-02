from django.conf import settings

USE_AUTH = getattr(settings, "SLR_USE_AUTH", True)
