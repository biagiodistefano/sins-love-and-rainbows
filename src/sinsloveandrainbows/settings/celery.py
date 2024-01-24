from .base import TIME_ZONE
from decouple import config

CELERY_BROKER_URL = config("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["application/json", "application/x-python-serialize"]
CELERY_RESULT_EXTENDED = True
CELERY_TASK_SERIALIZER = "pickle"
CELERY_RESULT_SERIALIZER = "pickle"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_ALWAYS_EAGER = config("CELERY_TASK_ALWAYS_EAGER", cast=bool, default=False)
