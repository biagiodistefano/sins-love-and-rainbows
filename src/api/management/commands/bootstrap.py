"""A dev tool to run migrations and create a default superuser."""

import typing as t
from argparse import ArgumentParser

from django.contrib.auth.models import User
from django.core import management
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from wasabi import msg

from django.conf import settings


class Command(BaseCommand):
    help = "Runs the `migrate` command and creates a default superuser"

    def add_arguments(self, parser: ArgumentParser) -> None:
        pass

    def handle(self, *args: t.Any, **options: t.Any) -> None:
        management.call_command("migrate", no_input=True)
        try:
            User.objects.create_superuser(
                username=settings.DEFAULT_SUPERUSER_USERNAME,
                email=None,
                password=settings.DEFAULT_SUPERUSER_PASSWORD,
            )
            msg.good(
                f"Created superuser {settings.DEFAULT_SUPERUSER_USERNAME!r} "
                f"with password {settings.DEFAULT_SUPERUSER_PASSWORD!r}"
            )
            msg.warn(f"Please change your password immediately visiting <your-host>/{settings.ADMIN_URL}")
        except IntegrityError:
            msg.fail(f"User {settings.DEFAULT_SUPERUSER_USERNAME} already exists.")
        # management.call_command("collectstatic", no_input=True)
