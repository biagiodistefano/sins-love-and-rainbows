import typing as t
from argparse import ArgumentParser

from django.core.management.base import BaseCommand


from api.models import Party
from api import messages


class Command(BaseCommand):
    help = "Automatically load people from a *.txt file"

    def add_arguments(self, parser: ArgumentParser) -> None:
        pass

    def handle(self, *args: t.Any, **options: t.Any) -> None:
        party = Party.get_next()
        messages.send_invitation_messages(party)
