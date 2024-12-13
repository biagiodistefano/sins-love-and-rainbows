import requests
from celery import shared_task
from django.conf import settings
from django.contrib.sites.models import Site
from django.shortcuts import reverse

from api import models

PUSHOVER_URL = "https://api.pushover.net/1/messages.json"


@shared_task
def notify_admins_of_rsvp_change(person: models.Person, party: models.Party, rsvp: models.Invite) -> None:
    """
    Send an email notification to admins about an RSVP change.

    Args:
    person_name (str): The name of the person who changed their RSVP.
    party_edition (str): The edition of the party.
    rsvp_status (str): The new RSVP status.
    """

    site = Site.objects.get_current()
    party_url = f"https://{site.domain}" + reverse("party", kwargs={"edition": party.edition})

    subject = f"{person.get_full_name()} RSVP'd {rsvp.get_status_display()} to {party}"
    message = (
        f"{person.get_full_name()} has replied {rsvp.get_status_display()} to their invitation to {party}\n\n"
        f"View the party details at {party_url}"
    )

    data = dict(
        token=settings.PUSHOVER_TOKEN,
        user=settings.PUSHOVER_USER_KEY,
        message=message,
        title=subject,
        url=party_url,
        url_title=party.name,
    )
    requests.post(PUSHOVER_URL, data=data)


@shared_task
def notify_admins_of_item_change(item: models.Item, person: models.Person, action: str) -> None:
    site = Site.objects.get_current()
    party_url = f"https://{site.domain}" + reverse("party", kwargs={"edition": item.party.edition})

    subject = f"{person.get_full_name()} {action} {item.name} for {item.party}"
    message = (
        f"{person.get_full_name()} {action} {item.name} for {item.party}\n\n" f"View the party details at {party_url}"
    )

    data = dict(
        token=settings.PUSHOVER_TOKEN,
        user=settings.PUSHOVER_USER_KEY,
        message=message,
        title=subject,
        url=party_url,
        url_title=item.party.name,
    )
    requests.post(PUSHOVER_URL, data=data)


@shared_task
def notify_admins_of_ingredient_creation(ingredient: models.Ingredient, person: models.Person) -> None:
    site = Site.objects.get_current()
    ingredient_url = f"https://{site.domain}" + reverse("ingredient", kwargs={"pk": ingredient.pk})

    subject = f"{person.get_full_name()} created {ingredient.name}"
    message = f"{person.get_full_name()} created {ingredient.name}\n\n" f"View the ingredient at {ingredient_url}"

    data = dict(
        token=settings.PUSHOVER_TOKEN,
        user=settings.PUSHOVER_USER_KEY,
        message=message,
        title=subject,
        url=ingredient_url,
        url_title=ingredient.name,
    )
    requests.post(PUSHOVER_URL, data=data)
