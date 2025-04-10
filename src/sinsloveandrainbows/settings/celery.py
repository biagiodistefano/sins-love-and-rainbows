from .base import TIME_ZONE
from decouple import config




REDIS_HOST = config("REDIS_HOST", default="localhost")
REDIS_DB = config("REDIS_DB", default=0, cast=int)
CELERY_BROKER_URL = f"redis://{REDIS_HOST}:6379/{REDIS_DB}"
CELERY_ACCEPT_CONTENT = ["application/json", "application/x-python-serialize"]
CELERY_RESULT_EXTENDED = True
CELERY_TASK_SERIALIZER = "pickle"
CELERY_RESULT_SERIALIZER = "pickle"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_ALWAYS_EAGER = config("CELERY_TASK_ALWAYS_EAGER", cast=bool, default=False)
