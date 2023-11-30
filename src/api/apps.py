from django.apps import AppConfig
from django.conf import settings
from datetime import datetime


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        deploy_filepath = settings.BASE_DIR / 'deployments.txt'
        with deploy_filepath.open("a") as f:
            f.write(f"SLR Started on {datetime.now()}\n")
