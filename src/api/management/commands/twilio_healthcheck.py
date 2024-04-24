import typing as t
from argparse import ArgumentParser

from django.core.management.base import BaseCommand

from api import settings
from api.messages import send_whatsapp_message


class Command(BaseCommand):
    help = "Twilio healthcheck command."

    def add_arguments(self, parser: ArgumentParser) -> None:
        pass

    def handle(self, *args: t.Any, **options: t.Any) -> None:
        send_whatsapp_message(settings.MY_PHONE_NUMBER, "healthcheck")
