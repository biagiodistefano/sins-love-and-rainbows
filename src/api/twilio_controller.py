from django.conf import settings
from django.http import HttpResponse
from ninja_extra import api_controller, route
from twilio.request_validator import RequestValidator
from django.shortcuts import get_object_or_404
from . import models


@api_controller(prefix_or_class="/twilio", tags=["Twilio"])
class TwilioController:  # type: ignore

    @route.post('/status_callback', url_name='twilio_status_callback')
    def receive_status(self, request):
        # Validate the request comes from Twilio
        validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)

        # The URL that Twilio POSTed to
        url = request.build_absolute_uri()

        # The POST variables Twilio sent with the request
        post_vars = request.POST.dict()

        # The Twilio signature from the X-Twilio-Signature header
        signature = request.META.get('HTTP_X_TWILIO_SIGNATURE', '')

        # Validate the request
        if not validator.validate(url, post_vars, signature):
            return HttpResponse("Invalid signature", status=403)

        # Your logic to handle the callback data
        message_sid = request.POST.get('MessageSid', '')
        message_status = request.POST.get('MessageStatus', '')
        message_error = request.POST.get('ErrorCode', '')

        print(f"SID: {message_sid}, Status: {message_status}, Error: {message_error}")

        message = get_object_or_404(models.PersonalLinkSent, sid=message_sid)
        message.status = message_status
        message.error = bool(message_error)
        message.error_message = message_error
        message.save()

        return HttpResponse("OK", status=200)
