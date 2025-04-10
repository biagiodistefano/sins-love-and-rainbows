import os
import requests

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sinsloveandrainbows.settings")

import django

django.setup()

from sinsloveandrainbows.settings import PUSHOVER_TOKEN, PUSHOVER_USER_KEY

URL = "https://api.pushover.net/1/messages.json"


data = dict(
    token=PUSHOVER_TOKEN,
    user=PUSHOVER_USER_KEY,
    message="Hello from Python!",
    title="Test",
    url="https://sinsloveandrainbows.eu",
    url_title="Sins, Love, and Rainbows",
)


response = requests.post(URL, data=data)
