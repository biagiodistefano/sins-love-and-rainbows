from django.db.models.signals import post_save
from django.dispatch import receiver

from . import models
from .messages import TEMPLATES
from .tasks import send_due_messages


@receiver(post_save, sender=models.Invite)
def send_messages_on_invite_create(sender, instance: models.Invite, created: bool, **kwargs):
    if created:
        send_due_messages.delay(party=instance.party, dry=False)


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
    for title, (message, delta, send_threshold) in TEMPLATES.items():
        msg_instance, created = models.Message.objects.get_or_create(party=instance, title=title)
        if not created:
            continue
        msg_instance.text = message
        msg_instance.due_at = instance.date_and_time - delta
        msg_instance.send_threshold = send_threshold
        msg_instance.draft = False
        msg_instance.save()


@receiver(post_save, sender=models.Person)
def create_preferences(sender, instance: models.Person, created: bool, **kwargs):
    if created:
        models.Preferences.objects.create(person=instance)
