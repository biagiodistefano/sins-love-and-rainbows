from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.shortcuts import reverse

from api import models


def notify_admins_of_rsvp_change(person: models.Person, party: models.Party, rsvp: models.Invite) -> None:
    """
    Send an email notification to admins about an RSVP change.

    Args:
    person_name (str): The name of the person who changed their RSVP.
    party_edition (str): The edition of the party.
    rsvp_status (str): The new RSVP status.
    """

    site = Site.objects.get_current()
    party_url = f"https://{site.domain}" + reverse('party', kwargs={"edition": party.edition})

    subject = f"{person.get_full_name()} RSVP'd {rsvp.get_status_display()} to {party}"
    message = (
        f"{person.get_full_name()} has replied {rsvp.get_status_display()} to their invitation to {party}\n\n"
        f"View the party details at {party_url}")

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [admin[1] for admin in settings.ADMINS],
        fail_silently=True,
    )
