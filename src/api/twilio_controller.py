import logging

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from ninja_extra import api_controller, route
import requests


from . import messages, models, settings
from .auth import TwilioAuth

logger = logging.getLogger("twilio_whatsapp")


@api_controller(prefix_or_class="/twilio", tags=["Twilio"], auth=TwilioAuth())
class TwilioController:  # type: ignore
    @route.post("/status_callback", url_name="twilio_status_callback")
    def receive_status(self, request: HttpRequest):
        # Your logic to handle the callback data
        message_sid = request.POST.get("MessageSid", "")
        message_status = request.POST.get("MessageStatus", "")
        message_error = request.POST.get("ErrorCode", "")
        message = get_object_or_404(models.MessageSent, sid=message_sid)
        message.status = message_status
        message.error = bool(message_error)
        if message.error:
            message.error_message = message_error
        message.save()

        return HttpResponse("OK", status=200)

    @route.post("/inbound", url_name="twilio_inbound")
    def receive_message(self, request: HttpRequest):
        from_number = request.POST.get("From", "")
        clean_number = from_number.replace("whatsapp:", "")
        if clean_number == settings.MY_PHONE_NUMBER:
            return admin_logic(request)
        body = request.POST.get("Body", "")
        logger.info(f"Received message from {clean_number}: {body}")

        person = get_object_or_404(models.Person, phone_number=clean_number)

        if body.lower().strip() == "stop":
            person.preferences.whatsapp_notifications = False
            person.preferences.save()
            logger.info(f"Stopped WhatsApp notifications for {person}")
            messages.send_whatsapp_message(
                to=clean_number, body="You will no longer receive WhatsApp notifications from us. Send START to resume."
            )
            return HttpResponse("OK", status=200)
        elif body.lower().strip() == "start":
            person.preferences.whatsapp_notifications = True
            person.preferences.save()
            logger.info(f"Started WhatsApp notifications for {person}")
            messages.send_whatsapp_message(
                to=clean_number, body="You will now receive WhatsApp notifications from us. Send STOP to unsubscribe."
            )
            return HttpResponse("OK", status=200)
        else:
            messages.send_whatsapp_message(
                to=clean_number, body="Sorry, I don't understand that command. Send STOP to unsubscribe."
            )
            return HttpResponse("OK", status=200)


def admin_logic(request: HttpRequest) -> HttpResponse:
    media_content_type = request.POST.get("MediaContentType0", None)
    if media_content_type == "text/vcard":
        logger.info("Received vCard")
        media_url = request.POST.get("MediaUrl0")
        try:
            r = handle_vcard(requests.get(media_url).content.decode("utf-8"))
            logger.info(f"Created {r} people")
            messages.send_whatsapp_message(to=settings.MY_PHONE_NUMBER, body=f"Created {r} people")
        except Exception as e:
            logger.error(f"Error while handling vCard: {e}")
            messages.send_whatsapp_message(to=settings.MY_PHONE_NUMBER, body=f"Error while handling vCard: {e}")

        return HttpResponse("OK", status=200)
    return HttpResponse("OK", status=200)


def handle_vcard(vcard: str) -> int:
    vcards = vcard.split("END:VCARD")
    extracted_data = []
    for vcard in vcards:
        data = {}
        for line in vcard.split("\n"):
            if line.startswith("N:"):
                last_name, first_name = line[2:].strip().split(";")
                data["first_name"] = first_name
                data["last_name"] = last_name
                data["username"] = f"{first_name.lower()}.{last_name.lower()}"
            elif line.startswith("TEL;"):
                # for some reason when using bulk create it's not automatic
                data["phone_number"] = models.PhoneNumberField.validate_phone_number(line.split(":")[1].strip())
            elif line.startswith("EMAIL;"):
                data["email"] = line.split(":")[1].strip()
        if data:
            extracted_data.append(data)
    # note: bulk_create doesn't call save() so signals aren't triggered, so we have to go one by one
    for data in extracted_data:
        models.Person.objects.create(**data)
    return len(extracted_data)
