import logging
import time

from django.conf import settings
from django.contrib.sites.models import Site
from django.db.models import Q
from django.shortcuts import reverse
from twilio.rest import Client as TwilioClient
from twilio.rest.api.v2010.account.message import MessageInstance

from . import models

logger = logging.getLogger("twilio_whatsapp")

TEMPLATES = {
    "slr_personal_link": """Your personal link to access our upcoming party is {url}

Do not share it with anyone else, it belongs to you!""",

    "slr_invitation": """Hi, {name}!

This is your personal link for our upcoming Party!

{url}

Don't share this link with anyone else, it's only yours!""",
    "slr_invitation_2": """Hi, {name}!

You are invited to *{party}*!

Here's your *personal* link to manage your invitation:

{url}

Don't share this link with anyone else, it's only yours!"""
}

message_statuses = ["accepted", "scheduled", "canceled", "queued", "sending",
                    "sent", "failed", "delivered", "undelivered", "receiving", "received", "read"]


def send_whatsapp_message(to: str, body: str) -> MessageInstance | None:
    if settings.DEBUG and to not in settings.DEBUG_NUMBERS_ALLOWED:
        return None
    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    from_whatsapp_number = settings.TWILIO_FROM_WHATSAPP_NUMBER
    client = TwilioClient(account_sid, auth_token)
    callback_url = reverse('slr-api:twilio_status_callback')
    message = client.messages.create(
        body=body,
        from_=f"whatsapp:{from_whatsapp_number}",
        to=f"whatsapp:{to}",
        status_callback="http://5179-2001-871-25c-ec13-b10f-47bd-fe9d-12cf.ngrok-free.app" + callback_url,
    )
    return message


def send_invitation_messages(party: models.Party, dry: bool = True, wait: bool = False, refresh: float = 5.0, force: bool = False) -> None:
    site = Site.objects.get_current()
    party_url = f"https://{site.domain}" + reverse('party', kwargs={"edition": party.edition})
    invites = party.invite_set.filter(Q(status__in=["Y", "M"]) | Q(status__isnull=True)).prefetch_related('person')
    sent = []
    for invite in invites:
        person = invite.person
        if (pls := models.PersonalLinkSent.objects.filter(party=party, person=person, sent=True).first()) and not force:
            sent.append(pls)
            logger.info(f"Skipping {person}: Already sent (status: {pls.status})")
            continue
        personal_url = f"{party_url}?visitor_id={str(person.pk)}"
        phone_number = person.clean_phone_number
        if not phone_number:
            continue
        if not phone_number.startswith("+"):
            phone_number = f"+{phone_number}"
        log_msg = f"{party}: Sending personal link to {person} ({phone_number})"
        if dry:
            print(f"[DRY] {log_msg}")
            continue
        try:
            message = send_whatsapp_message(
                to=phone_number, body=TEMPLATES["slr_invitation_2"].format(
                    name=person.first_name, party=str(party), url=personal_url
                )
            )
        except Exception as e:
            logger.error(f"Error sending message to {person}: {e}")
            models.PersonalLinkSent.objects.create(
                party=party, person=person, error=True, error_message=str(e)
            )
            continue
        if not message:
            continue
        pls = models.PersonalLinkSent.objects.create(party=party, person=person, sent=True, sid=message.sid)
        sent.append(pls)
        logger.info(log_msg)
    if wait:
        print("Refreshing statuses...")
        time.sleep(refresh)
        for pls in sent:
            pls.refresh_from_db()
            logger.info(f"{pls.person}: {pls.status}")
