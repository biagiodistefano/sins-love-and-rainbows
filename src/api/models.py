import urllib.parse
import uuid
from typing import Optional

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from markdownfield.models import MarkdownField, RenderedMarkdownField
from markdownfield.validators import VALIDATOR_STANDARD


class LowerCharField(models.CharField):
    def get_prep_value(self, value: str | None) -> str | None:
        value = super().get_prep_value(value)
        return value if value is None else value.lower()


class Person(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    password = models.CharField(_('password'), max_length=128, blank=True, null=True)
    phone_number = models.CharField(null=True, blank=True, db_index=True, max_length=128)
    from_abroad = models.BooleanField(default=False, db_index=True)
    in_broadcast = models.BooleanField(default=True, db_index=True)

    msg_template = (
        "Hi!\n\n"
        "This is your *personal* link for our upcoming party!\n {link}\n\n"
        "Don't share this link with anyone else, it's only yours!"
    )

    def whatsapp_message_url(self) -> str | None:
        if self.phone_number is None:
            return None
        party = Party.get_next()
        if not party:
            return None
        link = f"https://sinsloveandrainbows.eu/party/{party.edition}?visitor_id={str(self.id)}"
        msg = self.msg_template.format(link=link)
        urlencoded_msg = urllib.parse.quote(msg)
        return f"https://wa.me/{self.clean_phone_number}?text={urlencoded_msg}"

    @property
    def clean_phone_number(self) -> str | None:
        if not self.phone_number:
            return None
        return self.phone_number.replace("+", "").replace(" ", "")

    def __str__(self):
        return self.get_full_name()

    class Meta:
        verbose_name_plural = 'people'
        ordering = ['first_name', 'last_name']

    @property
    def full_name(self) -> str:
        return self.get_full_name()


class Party(models.Model):
    name = models.CharField(max_length=30, db_index=True, unique=True)
    edition = LowerCharField(max_length=30, db_index=True, unique=True)
    date_and_time = models.DateTimeField(db_index=True)
    location = models.CharField(max_length=120, db_index=True, null=True, blank=True)
    description = MarkdownField(
        rendered_field='description_rendered', validator=VALIDATOR_STANDARD, default="",
        blank=True
    )  # noqa: E501
    description_rendered = RenderedMarkdownField(null=True, blank=True)
    logo = models.ImageField(upload_to='logos', null=True, blank=True)
    closed = models.BooleanField(default=False, db_index=True)

    @classmethod
    def get_next(cls) -> Optional['Party']:
        return cls.objects.filter(date_and_time__gte=timezone.now(), closed=False).earliest(
            'date_and_time'
        )

    @property
    def logo_url(self) -> str | None:
        return self.logo.url if self.logo else None

    def invite(self, person: Person) -> 'Invite':
        instance, _ = Invite.objects.get_or_create(person=person, party=self)
        return instance

    def uninvite(self, person: Person) -> None:
        Invite.objects.filter(person=person, party=self).delete()

    def allergy_list(self) -> list[str]:
        invites = self.invite_set.filter(status='Y').prefetch_related('person__allergy_set__ingredient')
        return list(
            set(
                [allergy.ingredient.name for invite in invites for allergy in
                 invite.person.allergy_set.all()]
            )
        )  # noqa: E501

    def from_abroad_count(self) -> int:
        return self.invite_set.filter(person__from_abroad=True, status__in=("Y", "M")).count()

    def people(self) -> models.QuerySet:
        return Person.objects.filter(invite__party=self)

    def not_invited_people(self) -> list[Person]:
        return list(Person.objects.exclude(invite__party=self))

    def yes_people(self) -> models.QuerySet:
        return self.invite_set.filter(status='Y').prefetch_related('person')

    def maybe_people(self) -> models.QuerySet:
        return self.invite_set.filter(status='M').prefetch_related('person')

    def no_people(self) -> models.QuerySet:
        return self.invite_set.filter(status='N').prefetch_related('person')

    def yes_count(self) -> int:
        return self.yes_people().count()

    def no_count(self) -> int:
        return self.no_people().count()

    def maybe_count(self) -> int:
        return self.maybe_people().count()

    def invite_summary(self) -> dict[str, int]:
        return {
            "yes": self.yes_count(),
            "maybe": self.maybe_count(),
            "no": self.no_count(),
            "from_abroad": self.from_abroad_count(),
        }

    def food_items(self) -> models.QuerySet:
        return self.item_set.filter(category='F').prefetch_related('assigned_to')

    def drink_items(self) -> models.QuerySet:
        return self.item_set.filter(category='D').prefetch_related('assigned_to')

    def other_items(self) -> models.QuerySet:
        return self.item_set.filter(category='O').prefetch_related('assigned_to')

    def iter_items(self) -> list[tuple[str, models.QuerySet]]:
        return [
            ("Food", self.food_items()),
            ("Drink", self.drink_items()),
            ("Other", self.other_items()),
        ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'parties'
        ordering = ['-date_and_time']


class Invite(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    party = models.ForeignKey(Party, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=1, choices=((None, 'No response'), ('Y', 'Yes'), ('N', 'No'), ('M', 'Maybe')), default=None,
        db_index=True, null=True, blank=True
    )  # noqa: E501
    last_updated = models.DateTimeField(auto_now=True, db_index=True)

    @property
    def party_edition(self) -> str:
        return self.party.edition

    def __str__(self):
        return f"{self.person} @ {self.party}: {self.status}"

    class Meta:
        unique_together = ('person', 'party')

        indexes = [
            models.Index(fields=['person', 'party']),
        ]
        ordering = ['-status', 'person__first_name', 'person__last_name']


class Ingredient(models.Model):
    name = LowerCharField(max_length=30, db_index=True, unique=True)
    items = models.ManyToManyField('Item', blank=True)

    def __str__(self):
        return self.name


class Allergy(models.Model):
    ingredient = models.OneToOneField(Ingredient, on_delete=models.CASCADE)
    people = models.ManyToManyField(Person)

    def __str__(self):
        return self.ingredient.name

    class Meta:
        verbose_name_plural = 'allergies'


class Message(models.Model):
    party = models.ForeignKey(Party, on_delete=models.CASCADE)
    text = MarkdownField(rendered_field='text_rendered', validator=VALIDATOR_STANDARD)
    text_rendered = RenderedMarkdownField()
    sent_at = models.DateTimeField(db_index=True, null=True, blank=True)
    sent_to = models.ManyToManyField(Person)

    @property
    def party_edition(self) -> str:
        return self.party.edition

    def send(self, include_declined: bool = False) -> None:
        for invite in self.party.invite_set.filter(
            status__in=('Y', 'M', 'N') if include_declined else ('Y', 'M')
        ):
            # TODO: actually send the message
            self.sent_to.add(invite.person)
        self.sent_at = timezone.now()
        self.save()

    def sent_stats(self) -> str:
        sent_to_count = self.sent_to.count()
        not_sent_to_count = self.party.invite_set.all().count() - sent_to_count
        return f"{sent_to_count}/{not_sent_to_count} sent/not sent"


class ExternalLink(models.Model):
    party = models.ForeignKey(Party, on_delete=models.CASCADE)
    name = models.CharField(max_length=30, db_index=True)
    url = models.URLField(db_index=True)
    description = models.CharField(max_length=250, db_index=True, null=True, blank=True)

    @property
    def party_edition(self) -> str:
        return self.party.edition

    def __str__(self):
        return f"{self.name} @ {self.party}: {self.url}"


class Item(models.Model):
    party = models.ForeignKey(Party, on_delete=models.CASCADE)
    category = models.CharField(max_length=30, db_index=True, choices=(('F', 'Food'), ('D', 'Drink'), ('O', 'Other')))
    name = models.CharField(max_length=120, db_index=True)
    quantity = models.CharField(max_length=30, db_index=True, null=True, blank=True)
    description = models.CharField(max_length=250, db_index=True, null=True, blank=True)
    url = models.URLField(db_index=True, null=True, blank=True)
    ingredients = models.ManyToManyField(Ingredient, blank=True)
    assigned_to = models.ManyToManyField(Person, blank=True)

    @property
    def allergic_people(self) -> models.QuerySet:
        return self.party.people().filter(allergy__ingredient__in=self.ingredients.all())

    def allergens(self) -> list[str]:
        allergen_people = self.party.people().filter(allergy__ingredient__in=self.ingredients.all())
        return [i.name for i in Ingredient.objects.filter(allergy__person__in=allergen_people)]

    def assign_to(self, person: Person) -> None:
        if self.party.invite_set.filter(person=person, status__in=('Y', 'M')).exists():
            self.assigned_to.add(person)
            self.save()
            return
        raise ValueError(f"{person} is not invited to {self.party}")

    @property
    def party_edition(self) -> str:
        return self.party.edition

    def __str__(self):
        return f"{self.name} @ {self.party}"

    class Meta:
        indexes = [
            models.Index(fields=['party', 'category']),
        ]


class PartyFile(models.Model):
    party = models.ForeignKey(Party, on_delete=models.CASCADE)
    name = models.CharField(max_length=30, db_index=True)
    file = models.FileField(upload_to='files', db_index=True)
    description = models.CharField(max_length=250, db_index=True, null=True, blank=True)

    @property
    def party_edition(self) -> str:
        return self.party.edition

    @property
    def url(self) -> str:
        return self.file.url

    def __str__(self):
        return f"{self.file} @ {self.party}"


@receiver(post_save, sender=Party)
def create_invite(sender, instance, created, **kwargs):
    if created:
        for person in Person.objects.all():
            Invite.objects.create(person=person, party=instance, status=None)


def generate_short_url() -> str:
    return str(uuid.uuid4()).split("-")[0]


class ShortUrl(models.Model):
    short_url = models.CharField(max_length=16, unique=True, db_index=True, default=generate_short_url)
    url = models.URLField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.short_url} -> {self.url}"
