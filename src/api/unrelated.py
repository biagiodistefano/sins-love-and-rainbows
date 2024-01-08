from django.core.mail import EmailMessage
from celery import shared_task
from django.conf import settings


PRESCRIPTION_REQUEST = """
Good morning,

I am writing to you because I need a prescription for Isoptin 40mg. Would you please be so kind to put it on my e-card?
If possible 2x50 packages like last time.

Thank you in advance!

Kind regards,
Biagio Distefano
""".strip()


@shared_task
def send_prescription_email() -> None:
    email_msg = EmailMessage(
        subject="Prescription for Isoptin 40",
        body=PRESCRIPTION_REQUEST,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=["Office@teampraxis.wien"],
        bcc=["me@biagiodistefano.io"]
        # [admin[1] for admin in settings.ADMINS],
    )
    email_msg.send(fail_silently=True)
