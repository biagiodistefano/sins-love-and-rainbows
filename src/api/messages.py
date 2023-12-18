import logging

from celery import shared_task
from django.conf import settings
from django.contrib.sites.models import Site
from django.db.models import Q
from django.shortcuts import get_object_or_404, reverse
from twilio.rest import Client

from . import models

logger = logging.getLogger("twilio_whatsapp")

TEMPLATES = {
    "slr_personal_link": """Your personal link to access our upcoming party is {url}

Do not share it with anyone else, it belongs to you!""",

    "slr_invitation": """Hi, {name}!

This is your personal link for our upcoming Party!

{url}

Don't share this link with anyone else, it's only yours!"""
}


def send_whatsapp_message(to: str, body: str) -> str | None:
    if settings.DEBUG and to not in settings.DEBUG_NUMBERS_ALLOWED:
        return None
    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    from_whatsapp_number = settings.TWILIO_FROM_WHATSAPP_NUMBER
    client = Client(account_sid, auth_token)
    message = client.messages.create(
        body=body,
        from_=f"whatsapp:{from_whatsapp_number}",
        to=f"whatsapp:{to}"
    )
    return message.sid


@shared_task
def send_message(msg_id: int, include_declined: bool = False) -> None:
    message: models.Message = get_object_or_404(models.Message, pk=msg_id)
    people = message.party.invite_set.filter(status__in=["Y", "M"] if not include_declined else ["Y", "M", "N"])
    for person in people:
        if models.MessageLog.objects.filter(message=message, person=person, sent=True).exists():
            continue
        try:
            phone_number = person.clean_phone_number
            if not phone_number:
                continue
            if not phone_number.startswith("+"):
                phone_number = f"+{phone_number}"
            sid = send_whatsapp_message(to=phone_number, body=message.text)
            models.MessageLog.objects.create(message=message, person=person, sid=sid, sent_via="W", sent=True)
        except Exception as e:
            logger.error(f"Error sending message to {person}: {e}")
            models.MessageLog.objects.create(
                message=message, person=person, error=True, sent_via="W", error_message=str(e)
            )


def send_invitation_messages(party: models.Party, dry: bool = True) -> None:
    site = Site.objects.get_current()
    party_url = f"https://{site.domain}" + reverse('party', kwargs={"edition": party.edition})
    invites = party.invite_set.filter(Q(status__in=["Y", "M"]) | Q(status__isnull=True)).prefetch_related('person')
    for invite in invites:
        person = invite.person
        if models.PersonalLinkSent.objects.filter(party=party, person=person, sent=True).exists():
            continue
        try:
            personal_url = f"{party_url}?visitor_id={str(person.pk)}"
            phone_number = person.clean_phone_number
            if not phone_number:
                continue
            if not phone_number.startswith("+"):
                phone_number = f"+{phone_number}"
            log_msg = f"{party}: Sending personal link to {person} ({phone_number})"
            if dry:
                log_msg = f"[DRY] {log_msg}"
                print(log_msg)
            sid = None
            if not dry:
                logger.info(log_msg)
                sid = send_whatsapp_message(
                    to=phone_number, body=TEMPLATES["slr_invitation"].format(name=person.first_name, url=personal_url)
                    )
            if not sid:
                continue
            models.PersonalLinkSent.objects.create(party=party, person=person, sent=True, sid=sid)
        except Exception as e:
            logger.error(f"Error sending message to {person}: {e}")
            models.PersonalLinkSent.objects.create(
                party=party, person=person, error=True, error_message=str(e)
            )
