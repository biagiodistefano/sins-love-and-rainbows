import typing as t
from argparse import ArgumentParser

from django.core.management.base import BaseCommand


from api.models import Party
from api import messages


class Command(BaseCommand):
    help = "Automatically load people from a *.txt file"

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("--no-dry", action="store_true", help="Actually send the messages", default=False)
        parser.add_argument("--wait", action="store_true", help="Wait between messages", default=False)

    def handle(self, *args: t.Any, **options: t.Any) -> None:
        party = Party.get_next()
        dry = not options["no_dry"]
        messages.send_invitation_messages(party, dry=dry, wait=options["wait"])
