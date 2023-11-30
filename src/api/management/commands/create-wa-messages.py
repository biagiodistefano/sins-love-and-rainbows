import typing as t
from argparse import ArgumentParser

from django.core.management.base import BaseCommand
import urllib.parse

from ...models import Party


class Command(BaseCommand):
    help = "Automatically load people from a *.txt file"

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("--edition", type=str, help="The edition", default="people.txt")

    def handle(self, *args: t.Any, **options: t.Any) -> None:
        party = Party.objects.get(edition=options["edition"])

        msg_template = ("Hi!\n\n"
                        "This is your **personal** link for our upcoming party!\n\n {link}\n\n"
                        "Don't share this link with anyone else, it's only yours!")

        for person in party.people():
            link = f"https://sinsloveandrainbows.eu/party/{party.edition}?visitor_id={str(person.id)}"
            msg = msg_template.format(link=link)
            urlencoded_msg = urllib.parse.quote(msg)
            if person.phone_number:
                phone = person.phone_number.replace("+", "")
                print(f"{person.get_full_name()}: https://wa.me/{phone}?text={urlencoded_msg}")
