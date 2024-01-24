# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
from .base import BASE_DIR, CURRENT_BRANCH

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / f'{CURRENT_BRANCH.replace("/", "-")}.sqlite3',
    }
}
