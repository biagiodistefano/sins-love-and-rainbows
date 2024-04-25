from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"

    def ready(self):
        from . import signals  # noqa: F401
        from .tasks import set_inbound_webhook

        set_inbound_webhook()
