import logging
import time

from celery import shared_task
from django.contrib.sites.models import Site
from django.db.models import Q
from django.shortcuts import reverse
from django.utils import timezone

from . import models
from .messages import send_whatsapp_message
from .unrelated import send_prescription_email  # noqa: F401

logger = logging.getLogger("twilio_whatsapp")


@shared_task
def send_due_messages(
    party: models.Party | None = None, dry: bool = True, wait: bool = False, refresh: float = 5.0, force: bool = False
) -> None:
    if party is None:
        party = models.Party.get_next()
    site = Site.objects.get_current()
    party_url = f"https://{site.domain}" + reverse('party', kwargs={"edition": party.edition})
    sent = []
    messages = models.Message.objects.filter(party=party, due_at__lte=timezone.now(), draft=False).order_by("due_at")
    recipents = _get_recipients(party)
    for person in recipents:
        for message in messages:
            if (msg := models.MessageSent.objects.filter(
                message=message, party=party, person=person, sent=True
            ).first()) and not force:
                sent.append(msg)
                logger.info(f"Skipping {person}: Already sent (status: {msg.status})")
                continue
            personal_url = f"{party_url}?visitor_id={str(person.pk)}"
            log_msg = f"{party}: Sending {message.title} to {person} ({person.phone_number})"
            if dry:
                print(f"[DRY] {log_msg}")
                continue
            try:
                twilio_message = send_whatsapp_message(
                    to=person.phone_number, body=message.text.format(
                        name=person.first_name, party=str(party), url=personal_url
                    )
                )
            except Exception as e:
                logger.error(f"Error sending message to {person}: {e}")
                models.MessageSent.objects.create(
                    party=party, person=person, error=True, error_message=str(e)
                )
                continue
            if not twilio_message:
                continue
            msg_sent = models.MessageSent.objects.create(
                message=message, party=party, person=person, sent=True, sid=twilio_message.sid
            )
            sent.append(msg_sent)
            logger.info(log_msg)
    if wait and sent:
        print("Refreshing statuses...")
        time.sleep(refresh)
        for pls in sent:
            pls.refresh_from_db()
            logger.info(f"{pls.person}: {pls.status}")


def _get_recipients(party: models.Party) -> list[models.Person]:
    return [
        invite.person
        for invite in party.invite_set.filter(
            (Q(status__in=["Y", "M"]) | Q(status__isnull=True)) &
            Q(person__preferences__whatsapp_notifications=True) & Q(person__phone_number__isnull=False)
        ).prefetch_related('person')
    ]
