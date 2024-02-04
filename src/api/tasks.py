import logging
import time

from celery import shared_task
from django.contrib.sites.models import Site
from django.db.models import F, Q
from django.shortcuts import reverse
from django.utils import timezone
from twilio.rest.api.v2010.account.message import MessageInstance

from . import models
from .messages import send_whatsapp_message as _send_whatsapp_message

logger = logging.getLogger("twilio_whatsapp")


@shared_task
def send_due_messages(
    party: models.Party | None = None,
    dry: bool = True,
    wait: bool = False,
    refresh: float = 5.0,
    force: bool = False,
    filter_recipients: list[models.Person] | None = None,
    filter_messages: list[models.Message] | None = None,
) -> None:
    if party is None:
        party = models.Party.get_next()
    site = Site.objects.get_current()
    party_url = f"https://{site.domain}" + reverse("party", kwargs={"edition": party.edition})
    sent = []
    current_time = timezone.now()
    messages = (
        models.Message.objects.filter(party=party, due_at__lte=current_time, draft=False, autosend=True)
        .exclude(Q(send_threshold__isnull=False) & Q(due_at__lt=current_time - F("send_threshold")))
        .order_by("due_at")
        .prefetch_related("template")
    )
    if filter_messages:
        messages = messages.filter(pk__in=[msg.pk for msg in filter_messages])
    recipents = _get_recipients(party, filter_recipients)
    for person, rsvp in recipents:
        for message in messages:
            if (
                msg := models.MessageSent.objects.filter(message=message, party=party, person=person, sent=True).first()
            ) and not force:
                sent.append(msg)
                logger.info(f"Skipping {person}: Already sent (status: {msg.status})")
                continue
            if message.title != "Invitation" and rsvp is None and (party.date_and_time - current_time).days < 7:
                logger.info(f"Skipping {person}: Has not RSVP'd and event is less than 6 days away")
                continue
            personal_url = f"{party_url}?visitor_id={str(person.pk)}"
            log_msg = f"{party}: Sending {message.title} to {person} ({person.phone_number})"
            if dry:
                print(f"[DRY] {log_msg}")
                continue
            try:
                variables = dict(name=person.first_name, party=str(party), url=personal_url)
                twilio_message = send_whatsapp_message(
                    to=person.phone_number,
                    body=message.template.cleaned_text(variables=variables)
                    if message.template
                    else message.text.format(**variables),  # noqa: E501
                    content_sid=message.template.sid if message.template else None,
                    variables=message.template.cleaned_variables(variables) if message.template else None,
                )
            except Exception as e:
                logger.error(f"Error sending message to {person}: {e}")
                models.MessageSent.objects.create(
                    party=party, person=person, error=True, error_message=str(e), sent_via="W"
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


def _get_recipients(
    party: models.Party,
    filter_recipients: list[models.Person] | None = None,
) -> list[tuple[models.Person, str | None]]:
    conditions = (
        (Q(status__in=["Y", "M"]) | Q(status__isnull=True))
        & Q(person__preferences__whatsapp_notifications=True)
        & Q(person__phone_number__isnull=False)
    )
    if filter_recipients:
        conditions &= Q(person__in=filter_recipients)
    return [(invite.person, invite.status) for invite in party.invite_set.filter(conditions).prefetch_related("person")]


@shared_task
def send_whatsapp_message(
    to: str, body: str, content_sid: None | str = None, variables: dict | None = None
) -> MessageInstance | None:
    return _send_whatsapp_message(to, body, content_sid, variables)


@shared_task
def submit_new_template(template: models.MessageTemplate) -> None:
    template.submit()
    logger.info(f"Submitted new template: {template}")
    template.refresh_from_db()
    template.request_approval()
    logger.info(f"Requested approval for new template: {template}")


@shared_task
def update_approval_statuses() -> None:
    for template in models.MessageTemplate.objects.filter(status="PENDING"):
        template.update_status()
        logger.info(f"Updated status for template: {template}")
