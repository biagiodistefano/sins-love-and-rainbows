import typing as t
from argparse import ArgumentParser

from django.core.management.base import BaseCommand

from ._helpers import create_test_party


class Command(BaseCommand):
    help = "Automatically load people from a *.txt file"

    def add_arguments(self, parser: ArgumentParser) -> None:
        pass

    def handle(self, *args: t.Any, **options: t.Any) -> None:
        create_test_party()
