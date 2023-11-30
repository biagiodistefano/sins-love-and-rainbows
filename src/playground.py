import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sinsloveandrainbows.settings")

import django

django.setup()

from api import models


me = models.Person.objects.get(username="biagio")
