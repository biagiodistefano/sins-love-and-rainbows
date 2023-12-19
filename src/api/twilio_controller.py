import logging

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from ninja_extra import api_controller, route

from . import models
from .auth import TwilioAuth
from . import messages

logger = logging.getLogger("twilio_whatsapp")


@api_controller(prefix_or_class="/twilio", tags=["Twilio"], auth=TwilioAuth())
class TwilioController:  # type: ignore

    @route.post('/status_callback', url_name='twilio_status_callback')
    def receive_status(self, request: HttpRequest):

        # Your logic to handle the callback data
        message_sid = request.POST.get('MessageSid', '')
        message_status = request.POST.get('MessageStatus', '')
        message_error = request.POST.get('ErrorCode', '')
        message = get_object_or_404(models.PersonalLinkSent, sid=message_sid)
        message.status = message_status
        message.error = bool(message_error)
        if message.error:
            message.error_message = message_error
        message.save()

        return HttpResponse("OK", status=200)

    @route.post('/inbound', url_name='twilio_inbound')
    def receive_message(self, request: HttpRequest):
        from_number = request.POST.get('From', '')
        clean_number = from_number.replace("whatsapp:", "")
        body = request.POST.get('Body', '')
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
                to=clean_number, body="Sorry, we don't understand that command. Send STOP to unsubscribe."
            )
            return HttpResponse("OK", status=200)
