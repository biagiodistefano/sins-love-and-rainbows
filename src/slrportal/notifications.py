from django.core.mail import send_mail
from django.conf import settings
from api import models


def notify_admins_of_rsvp_change(person: models.Person, party: models.Party, rsvp: models.Invite) -> None:
    """
    Send an email notification to admins about an RSVP change.

    Args:
    person_name (str): The name of the person who changed their RSVP.
    party_edition (str): The edition of the party.
    rsvp_status (str): The new RSVP status.
    """
    subject = f"{person.get_full_name()} RSVP'd {rsvp.get_status_display()} to {party}"
    message = (f"{person.get_full_name()} has updated their RSVP for {party}.\n"
               f"New status: {rsvp.get_status_display()}")

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [admin[1] for admin in settings.ADMINS],
        fail_silently=True,
    )
