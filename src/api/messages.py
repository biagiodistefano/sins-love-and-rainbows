import logging

from django.contrib.sites.models import Site
from django.shortcuts import reverse
from twilio.rest import Client as TwilioClient
from twilio.rest.api.v2010.account.message import MessageInstance

from . import settings

logger = logging.getLogger("twilio_whatsapp")

TEMPLATES = {
    "slr_invitation": """Hi, {name}!

You are invited to *{party}*!

Here's your *personal* link to manage your invitation:

{url}

Don't share this link with anyone else, it's only yours!

(Send "stop" to unsubscribe)
""",
    "slr_reminder": """Hi, {name}!

This is just to remind you that are invited to *{party}*!

Here's your *personal* link to manage your invitation:

{url}

Don't share this link with anyone else, it's only yours!

(Send "stop" to unsubscribe)"""
}


# message_statuses = ["accepted", "scheduled", "canceled", "queued", "sending",
# "sent", "failed", "delivered", "undelivered", "receiving", "received", "read"]


def send_whatsapp_message(to: str, body: str) -> MessageInstance | None:
    if settings.DEBUG and to not in settings.DEBUG_NUMBERS_ALLOWED:
        return None
    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    from_whatsapp_number = settings.TWILIO_FROM_WHATSAPP_NUMBER
    client = TwilioClient(account_sid, auth_token)
    callback_path = reverse('slr-api:twilio_status_callback')
    callback_url = (settings.NGROK_URL or f"https://{Site.objects.get_current().domain}") + callback_path
    message = client.messages.create(
        body=body,
        from_=f"whatsapp:{from_whatsapp_number}",
        to=f"whatsapp:{to}",
        status_callback=callback_url,
    )
    return message
