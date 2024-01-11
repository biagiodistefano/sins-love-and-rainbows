import logging
from datetime import timedelta
from pathlib import Path

from dateutil.relativedelta import relativedelta
from django.contrib.sites.models import Site
from django.shortcuts import reverse
from twilio.rest import Client as TwilioClient
from twilio.rest.api.v2010.account.message import MessageInstance

from . import settings

logger = logging.getLogger("twilio_whatsapp")


def load_templates():
    template_dir = Path(__file__).parent / 'templates' / 'api'
    templates = {}
    delta_dict = {
        "Invitation": (relativedelta(months=1, hour=1), None),
        "2-week reminder": (relativedelta(weeks=2, hour=1), timedelta(days=1)),
        "1-week reminder": (relativedelta(weeks=1, hour=1), timedelta(days=1)),
        "Final reminder": (relativedelta(days=2, hour=1), timedelta(days=1)),
    }
    for file_path in template_dir.glob('*.txt'):
        with file_path.open('r') as file:
            content = file.read().strip()
        # Use the file stem (without extension) as the key and content as the value
        file_stem = file_path.stem
        templates[file_stem] = (content, *delta_dict.get(file_stem))
    return templates


TEMPLATES = load_templates()


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
