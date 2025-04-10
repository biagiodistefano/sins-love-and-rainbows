# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
from .base import BASE_DIR
from decouple import config

DB_NAME = config("DB_NAME", default="production")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db" / f'{DB_NAME}.sqlite3',
    }
}
