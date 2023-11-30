import typing as t
from argparse import ArgumentParser

from django.core.management.base import BaseCommand

from ._helpers import load_allergies, load_people


class Command(BaseCommand):
    help = "Automatically load people from a *.txt file"

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("--file", type=str, help="The file to load from", default="people.txt")
        parser.add_argument("--allergy-file", type=str, help="The file to load from", default="allergies.txt")

    def handle(self, *args: t.Any, **options: t.Any) -> None:
        load_people(options["file"])
        load_allergies(options["allergy_file"])
