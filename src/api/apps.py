from django.apps import AppConfig
from . import settings


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        from . import messages
        to = settings.MY_PHONE_NUMBER
        if to is None or settings.DEBUG:
            return
        messages.send_whatsapp_message(to, "Server is ready")
