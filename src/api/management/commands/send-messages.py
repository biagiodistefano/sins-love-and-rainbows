import typing as t
from argparse import ArgumentParser

from django.core.management.base import BaseCommand

from api import settings
from api.models import Party
from api.tasks import send_due_messages


class Command(BaseCommand):
    help = "Automatically load people from a *.txt file"

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("--no-dry", action="store_true", help="Actually send the messages", default=False)
        parser.add_argument("--wait", action="store_true", help="Wait between messages", default=False)
        parser.add_argument("--force", action="store_true", help="Force sending messages", default=False)
        parser.add_argument("--refresh", type=float, help="Refresh rate", default=5.0)
        parser.add_argument("--party", type=int, help="Party ID", default=None)

    def handle(self, *args: t.Any, **options: t.Any) -> None:
        if options["party"] is not None:
            party = Party.objects.get(id=options["party"], closed=False)
        else:
            party = Party.get_next()
        dry = not options["no_dry"]
        if not settings.DEBUG and not dry:
            a = input("Are you sure you want to send messages? [y/N] ")
            if a.lower() != "y":
                return
        print(f"Sending messages for {party} (dry: {dry})")
        send_due_messages(party, dry=dry, wait=options["wait"], refresh=options["refresh"], force=options["force"])
