from decouple import config


PUSHOVER_TOKEN = config("PUSHOVER_TOKEN", default="")
PUSHOVER_USER_KEY = config("PUSHOVER_USER_KEY", default="")
