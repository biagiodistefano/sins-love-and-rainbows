import json
import logging

from django.contrib.sites.models import Site
from django.shortcuts import reverse
from twilio.rest import Client as TwilioClient
from twilio.rest.api.v2010.account.message import MessageInstance

from . import settings

logger = logging.getLogger("twilio_whatsapp")


def send_whatsapp_message(
    to: str, body: str, content_sid: None | str = None, variables: dict | None = None
) -> MessageInstance | None:
    if settings.DEBUG and to not in settings.DEBUG_NUMBERS_ALLOWED:
        return None
    variables = variables or {}
    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    client = TwilioClient(account_sid, auth_token)
    callback_path = reverse("slr-api:twilio_status_callback")
    callback_url = (settings.NGROK_URL or f"https://{Site.objects.get_current().domain}") + callback_path
    kwargs = dict(
        body=body,
        from_=settings.TWILIO_SENDER_SID,
        content_variables=json.dumps(variables),
        to=f"whatsapp:{to}",
        status_callback=callback_url,
    )
    if content_sid is not None:
        kwargs["content_sid"] = content_sid
    message = client.messages.create(
        **kwargs,
    )
    return message
