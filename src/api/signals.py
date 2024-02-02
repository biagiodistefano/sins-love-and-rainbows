from django.db.models.signals import post_save
from django.dispatch import receiver

from . import models
from . import tasks
import logging


logger = logging.getLogger("twilio_whatsapp")


@receiver(post_save, sender=models.Invite)
def send_messages_on_invite_create(sender, instance: models.Invite, created: bool, **kwargs):
    if created:
        tasks.send_due_messages.delay(party=instance.party, dry=False, filter_recipients=[instance.person])


@receiver(post_save, sender=models.Party)
def create_invite(sender, instance: models.Party, created: bool, **kwargs):
    if created and not instance.private:
        post_save.disconnect(send_messages_on_invite_create, sender=models.Invite)

        try:
            for person in models.Person.objects.all():
                models.Invite.objects.create(person=person, party=instance, status=None)
        finally:
            # Reconnect the second receiver
            post_save.connect(send_messages_on_invite_create, sender=models.Invite)


@receiver(post_save, sender=models.Party)
def create_party_default_messages(sender, instance: models.Party, created: bool, **kwargs):
    for message_template in models.MessageTemplate.objects.filter(is_default_party_message=True):
        msg_instance, created = models.Message.objects.get_or_create(party=instance, title=message_template.title)
        if not created:
            continue
        msg_instance.text = message_template.text
        if message_template.send_delta is not None:
            msg_instance.due_at = instance.date_and_time - message_template.send_delta
        msg_instance.send_threshold = message_template.send_threshold
        msg_instance.draft = message_template.draft
        msg_instance.autosend = message_template.autosend
        msg_instance.save()


@receiver(post_save, sender=models.Person)
def create_preferences(sender, instance: models.Person, created: bool, **kwargs):
    if created:
        models.Preferences.objects.create(person=instance)


@receiver(post_save, sender=models.MessageTemplate)
def create_template_message(sender, instance: models.MessageTemplate, created: bool, **kwargs):
    try:
        if instance.draft:
            return
        tasks.submit_new_template(instance)
    except Exception as e:
        print(f"Error submitting template: {e}")
