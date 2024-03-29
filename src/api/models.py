import re
import urllib.parse
import uuid
from typing import Any, Optional

import requests
from django.contrib.auth.models import AbstractUser
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.db import models
from django.shortcuts import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from markdownfield.models import MarkdownField, RenderedMarkdownField
from markdownfield.validators import VALIDATOR_STANDARD
from requests.auth import HTTPBasicAuth

from . import settings


class PhoneNumberField(models.CharField):
    def __init__(self, *args, **kwargs) -> None:
        kwargs["max_length"] = 32  # Adjust as necessary
        super().__init__(*args, **kwargs)

    def clean(self, value: str | None, model_instance: Any) -> str | None:
        if value is None:
            return None
        value = super().clean(value, model_instance).strip()
        return self.validate_phone_number(value)

    @staticmethod
    def validate_phone_number(phone_number: str) -> str:
        if not phone_number.startswith("+"):
            raise ValidationError("Phone number must start with a '+'")

        # Remove spaces, dashes, and parentheses
        sanitized_number = re.sub(r"[ ()-]", "", phone_number).strip()

        # Check if sanitized number consists only of digits after '+'
        if not sanitized_number[1:].isdigit():
            raise ValidationError("Invalid phone number format")

        return sanitized_number


class StrippedCharField(models.CharField):
    def get_prep_value(self, value: str | None) -> str | None:
        value = super().get_prep_value(value)
        return value if value is None else value.strip()


class LowerCharField(StrippedCharField):
    def get_prep_value(self, value: str | None) -> str | None:
        value = super().get_prep_value(value)
        return value if value is None else value.lower()


class Person(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    password = models.CharField(_("password"), max_length=128, blank=True, null=True)
    phone_number = PhoneNumberField(null=True, blank=True, db_index=True)
    from_abroad = models.BooleanField(default=False, db_index=True)
    in_broadcast = models.BooleanField(default=True, db_index=True)
    allergies = models.ManyToManyField("Ingredient", blank=True, through="Allergy")

    msg_template = (
        "Hi!\n\n"
        "This is your *personal* link for our upcoming party!\n\n{link}\n\n"
        "Don't share this link with anyone else, it's only yours!"
    )

    def whatsapp_message_url(self) -> str | None:
        if self.phone_number is None:
            return None
        party = Party.get_next()
        if not party or not self.is_invited_to(party):
            return None
        link = f"https://{Site.objects.get_current().domain}" + reverse("party", args=[party.edition])
        query_params = {"visitor_id": str(self.id)}
        link += f"?{urllib.parse.urlencode(query_params)}"
        msg = self.msg_template.format(link=link)
        urlencoded_msg = urllib.parse.quote(msg)
        return f"https://wa.me/{self.phone_number[1:]}?text={urlencoded_msg}"

    def __str__(self):
        return self.get_full_name()

    class Meta:
        verbose_name_plural = "people"
        ordering = ["first_name", "last_name"]

    @property
    def full_name(self) -> str:
        return self.get_full_name()

    def get_display_name(self) -> str:
        users_with_same_first_name = Person.objects.filter(first_name=self.first_name).exclude(id=self.id)

        if not users_with_same_first_name:
            return self.first_name

        min_chars = 1
        while True:
            unique_last_name = True
            for user in users_with_same_first_name:
                if user.last_name.startswith(self.last_name[:min_chars]):
                    unique_last_name = False
                    break

            if unique_last_name:
                break
            min_chars += 1

            # Avoid infinite loop in cases of identical names
            if min_chars >= len(self.last_name):
                break

        return f"{self.first_name} {self.last_name[:min_chars]}".strip()

    def is_invited_to(self, party: "Party") -> bool:
        return party.invite_set.filter(person=self).exists()


class Preferences(models.Model):
    person = models.OneToOneField(Person, on_delete=models.CASCADE)
    whatsapp_notifications = models.BooleanField(default=True, db_index=True)
    email_notifications = models.BooleanField(default=False, db_index=True)

    class Meta:
        verbose_name_plural = "preferences"
        ordering = ["person__first_name", "person__last_name"]

    def __str__(self) -> str:
        return f"{self.person}'s preferences"


class Party(models.Model):
    name = models.CharField(max_length=128, db_index=True, unique=True)
    edition = LowerCharField(max_length=30, db_index=True, unique=True)
    date_and_time = models.DateTimeField(db_index=True)
    location = models.CharField(max_length=120, db_index=True, null=True, blank=True)
    description = MarkdownField(
        rendered_field="description_rendered", validator=VALIDATOR_STANDARD, default="", blank=True
    )  # noqa: E501
    description_rendered = RenderedMarkdownField(null=True, blank=True)
    logo = models.ImageField(upload_to="logos", null=True, blank=True)
    closed = models.BooleanField(default=True, db_index=True)
    private = models.BooleanField(default=False, db_index=True)
    max_people = models.PositiveSmallIntegerField(default=0, db_index=True)

    @classmethod
    def get_next(cls) -> Optional["Party"]:
        return cls.objects.filter(date_and_time__gte=timezone.now(), closed=False).earliest("date_and_time")

    @property
    def logo_url(self) -> str | None:
        return self.logo.url if self.logo else None

    def invite(self, person: Person) -> "Invite":
        instance, _ = Invite.objects.get_or_create(person=person, party=self)
        return instance

    def uninvite(self, person: Person) -> None:
        Invite.objects.filter(person=person, party=self).delete()

    def allergy_list(self) -> list[str]:
        invites = self.invite_set.filter(status="Y").prefetch_related("person__allergies")
        return list(set([allergy.name for invite in invites for allergy in invite.person.allergies.all()]))  # noqa: E501

    def from_abroad_count(self) -> int:
        return self.invite_set.filter(person__from_abroad=True, status__in=("Y", "M")).count()

    def people(self) -> models.QuerySet:
        return Person.objects.filter(invite__party=self)

    def not_invited_people(self) -> list[Person]:
        return list(Person.objects.exclude(invite__party=self))

    def yes_people(self) -> models.QuerySet:
        return self.invite_set.filter(status="Y").prefetch_related("person")

    def maybe_people(self) -> models.QuerySet:
        return self.invite_set.filter(status="M").prefetch_related("person")

    def no_people(self) -> models.QuerySet:
        return self.invite_set.filter(status="N").prefetch_related("person")

    def no_response_people(self) -> models.QuerySet:
        return self.invite_set.filter(status=None).prefetch_related("person")

    def yes_count(self) -> int:
        return self.yes_people().count()

    def no_count(self) -> int:
        return self.no_people().count()

    def maybe_count(self) -> int:
        return self.maybe_people().count()

    def no_response_count(self) -> int:
        return self.no_response_people().count()

    def invite_summary(self) -> dict[str, int]:
        return {
            "yes": self.yes_count(),
            "maybe": self.maybe_count(),
            "no": self.no_count(),
            "no_response": self.no_response_count(),
            "from_abroad": self.from_abroad_count(),
        }

    def food_items(self) -> models.QuerySet:
        return self.item_set.filter(category="F").prefetch_related("assigned_to")

    def drink_items(self) -> models.QuerySet:
        return self.item_set.filter(category="D").prefetch_related("assigned_to")

    def other_items(self) -> models.QuerySet:
        return self.item_set.filter(category="O").prefetch_related("assigned_to")

    def iter_items(self) -> list[tuple[str, models.QuerySet]]:
        return [
            ("Food", self.food_items()),
            ("Drink", self.drink_items()),
            ("Other", self.other_items()),
        ]

    def is_invited(self, person: Person) -> bool:
        return self.invite_set.filter(person=person).exists()

    def guest_list(self) -> dict[str, list[str]]:
        yes = [invite.person.get_display_name() for invite in self.yes_people().filter(show_in_guest_list=True)]
        private_yes_count = self.yes_people().filter(show_in_guest_list=False).count()
        if private_yes_count > 0:
            if yes:
                yes.append(f"+ {private_yes_count} other(s)")
            else:
                yes = [f"{private_yes_count} attending"]
        maybe = [invite.person.get_display_name() for invite in self.maybe_people().filter(show_in_guest_list=True)]
        private_maybe_count = self.maybe_people().filter(show_in_guest_list=False).count()
        if private_maybe_count > 0:
            if maybe:
                maybe.append(f"+ {private_maybe_count} other(s)")
            else:
                maybe = [f"{private_maybe_count} maybe"]
        return {
            "yes": yes,
            "maybe": maybe,
        }

    def get_people_with_no_items(self) -> models.QuerySet:
        # Get people who have RSVP'd 'Yes' or 'Maybe'
        rsvp_people = self.invite_set.filter(status__in=["Y", "M"]).values_list("person", flat=True)

        # Get people who have been assigned to items
        assigned_people = self.item_set.filter(assigned_to__isnull=False).values_list("assigned_to", flat=True)

        # Filter out people who have been assigned any items
        people_with_no_items = Person.objects.filter(id__in=rsvp_people).exclude(id__in=assigned_people)

        return people_with_no_items

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "parties"
        ordering = ["-date_and_time"]


class Invite(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    party = models.ForeignKey(Party, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=1,
        choices=((None, "No response"), ("Y", "Yes"), ("N", "No"), ("M", "Maybe")),
        default=None,
        db_index=True,
        null=True,
        blank=True,
    )  # noqa: E501
    last_updated = models.DateTimeField(auto_now=True, db_index=True)
    show_in_guest_list = models.BooleanField(default=False, db_index=True)

    @property
    def party_edition(self) -> str:
        return self.party.edition

    def __str__(self):
        return f"{self.person} @ {self.party.edition}: {self.status}"

    class Meta:
        unique_together = ("person", "party")

        indexes = [
            models.Index(fields=["person", "party"]),
        ]
        ordering = ["-party__date_and_time", "person__first_name", "person__last_name", "-status"]


class Ingredient(models.Model):
    name = LowerCharField(max_length=30, db_index=True, unique=True)
    items = models.ManyToManyField("Item", blank=True)
    allergic_people = models.ManyToManyField(Person, through="Allergy")

    def __str__(self):
        return self.name


class Allergy(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)

    def __str__(self):
        return self.ingredient.name

    class Meta:
        verbose_name_plural = "allergies"


class MessageBase(models.Model):
    title = models.CharField(max_length=30, db_index=True, null=True, blank=True)
    text = models.TextField(db_index=True, null=True, blank=True)
    send_threshold = models.DurationField(null=True, blank=True)  # how long after the due_at to still send the message
    draft = models.BooleanField(default=True, db_index=True)
    autosend = models.BooleanField(default=False, db_index=True)

    class Meta:
        abstract = True


def _default_variables() -> dict[str, str]:
    return {
        "party": "Sins, Love and Rainbows: Super Cool Edition",
        "url": "https://example.com/?visitor_id=1234",
        "name": "John",
    }


class MessageTemplate(MessageBase):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._original_text = self.text

    friendly_name = models.CharField(max_length=64, db_index=True, unique=True)
    language = models.CharField(max_length=5, db_index=True, default="en")
    variables = models.JSONField(default=_default_variables, blank=True, null=True)
    sid = models.CharField(max_length=34, null=True, blank=True, editable=False)
    status = models.CharField(
        max_length=25,
        db_index=True,
        null=True,
        blank=True,
        choices=(
            ("NOT_SUBMITTED", "NOT_SUBMITTED"),
            ("APPROVED", "APPROVED"),
            ("PENDING", "PENDING"),
            ("REJECTED", "REJECTED"),
        ),
        default="NOT_SUBMITTED",
    )
    send_delta = models.DurationField(null=True, blank=True)  # how long before the party to send the message
    rejection_reason = models.TextField(null=True, blank=True)
    is_default_party_message = models.BooleanField(default=False, db_index=True)
    category = models.CharField(
        max_length=30,
        db_index=True,
        null=True,
        blank=True,
        choices=(
            ("UTILITY", "UTILITY"),
            ("MARKETING", "MARKETING"),
            ("AUTHENTICATION", "AUTHENTICATION"),
        ),
        default="UTILITY",
    )
    CONTENT_URL = "https://content.twilio.com/v1/Content"
    APPROVAL_FETCH_URL = CONTENT_URL + "/{sid}/ApprovalRequests"
    APPROVAL_CREATE_URL = APPROVAL_FETCH_URL + "/whatsapp"
    AUTH = HTTPBasicAuth(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    def __str__(self):
        return self.friendly_name

    @property
    def approval_fetch_url(self) -> str:
        if not self.sid:
            raise ValueError("This message template has not been submitted to Twilio")
        return self.APPROVAL_FETCH_URL.format(sid=self.sid)

    @property
    def approval_create_url(self) -> str:
        if not self.sid:
            raise ValueError("This message template has not been submitted to Twilio")
        return self.APPROVAL_CREATE_URL.format(sid=self.sid)

    def to_twilio_json(self) -> dict:
        return {
            "friendly_name": self.friendly_name,
            "language": self.language,
            "variables": self.cleaned_variables(),
            "types": {
                "twilio/text": {
                    "body": self.cleaned_text(),
                }
            },
        }

    def cleaned_text(self, variables: dict | None = None) -> str:
        text = self.text
        placeholder_counter = 1
        keyword_occurrences = {}

        while True:
            found = False
            for keyword in (variables or self.variables).keys():
                if f"{{{keyword}}}" in text:
                    found = True
                    text = text.replace(f"{{{keyword}}}", f"{{{{{placeholder_counter}}}}}", 1)
                    keyword_occurrences[placeholder_counter] = keyword
                    placeholder_counter += 1
            if not found:
                break

        return text

    def cleaned_variables(self, variables: dict | None = None) -> dict[str, str]:
        keyword_occurrences = self._generate_keyword_occurrences(variables)
        new_variables = {str(k): (variables or self.variables)[v] for k, v in keyword_occurrences.items()}
        return new_variables

    def _generate_keyword_occurrences(self, variables: dict | None = None) -> dict[int, str]:
        text = self.text  # Assuming self.body contains the template text
        placeholder_counter = 1
        keyword_occurrences = {}

        while True:
            found = False
            for keyword in (variables or self.variables).keys():
                if f"{{{keyword}}}" in text:
                    found = True
                    text = text.replace(f"{{{keyword}}}", "", 1)
                    keyword_occurrences[placeholder_counter] = keyword
                    placeholder_counter += 1
            if not found:
                break

        return keyword_occurrences

    def submit(self) -> requests.Response:
        r = requests.post(self.CONTENT_URL, auth=self.AUTH, json=self.to_twilio_json())
        r.raise_for_status()
        sid = r.json()["sid"]
        MessageTemplate.objects.filter(pk=self.pk).update(sid=sid)  # update without signals
        return sid

    def request_approval(self) -> requests.Response:
        r = requests.post(
            self.approval_create_url, auth=self.AUTH, json={"name": self.friendly_name, "category": self.category}
        )
        r.raise_for_status()
        MessageTemplate.objects.filter(pk=self.pk).update(status="PENDING")  # update without signals
        return r

    def update_status(self) -> requests.Response:
        r = requests.get(self.approval_fetch_url, auth=self.AUTH)
        r.raise_for_status()
        status = r.json()["whatsapp"]["status"].upper()
        rejection_reason = r.json()["whatsapp"]["rejection_reason"]
        MessageTemplate.objects.filter(pk=self.pk).update(
            status=status, rejection_reason=rejection_reason
        )  # update without signals  # noqa: E501
        return r


class Message(MessageBase):
    party = models.ForeignKey(Party, on_delete=models.CASCADE)
    template = models.ForeignKey(MessageTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    text = MarkdownField(rendered_field="text_rendered", validator=VALIDATOR_STANDARD, default="", blank=True)
    text_rendered = RenderedMarkdownField()
    due_at = models.DateTimeField(db_index=True, null=True, blank=True)

    class Meta:
        ordering = ["-party__date_and_time", "-due_at"]
        index_together = [("party", "due_at", "draft", "autosend")]
        unique_together = [("party", "title")]

    @property
    def party_edition(self) -> str:
        return self.party.edition

    def __str__(self):
        if self.title:
            title = self.title
        else:
            title = self.text[:30]
        return f"{title} @ {self.party}"


class MessageSent(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    party = models.ForeignKey(Party, on_delete=models.CASCADE)
    sent = models.BooleanField(default=False, db_index=True)
    sent_at = models.DateTimeField(auto_now_add=True, db_index=True)
    sent_via = models.CharField(
        max_length=30,
        db_index=True,
        choices=(("W", "WhatsApp"), ("S", "SMS"), ("E", "Email"), ("T", "Telegram")),
        null=True,
        blank=True,
    )
    sid = models.CharField(max_length=34, null=True, blank=True)
    status = models.CharField(max_length=30, db_index=True, null=True, blank=True)
    error = models.BooleanField(default=False, db_index=True)
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Messages Sent"
        index_together = [
            ("message", "person", "party", "sent"),
        ]
        unique_together = [
            ("message", "person", "party", "sent_via"),
        ]

    def __str__(self) -> str:
        return f"[{self.party}] {self.message.title} -> {self.person} ({self.status})"


class ExternalLink(models.Model):
    parties = models.ManyToManyField(Party, blank=True)
    name = models.CharField(max_length=30, db_index=True)
    url = models.URLField(db_index=True)
    description = models.CharField(max_length=250, db_index=True, null=True, blank=True)

    def __str__(self):
        return f"{self.name}: {self.url}"


class Item(models.Model):
    party = models.ForeignKey(Party, on_delete=models.CASCADE)
    category = models.CharField(max_length=30, db_index=True, choices=(("F", "Food"), ("D", "Drink"), ("O", "Other")))
    name = StrippedCharField(max_length=120, db_index=True)
    quantity = StrippedCharField(max_length=30, db_index=True, null=True, blank=True)
    description = StrippedCharField(max_length=250, db_index=True, null=True, blank=True)
    url = models.URLField(db_index=True, null=True, blank=True)
    ingredients = models.ManyToManyField(Ingredient, blank=True)
    assigned_to = models.ManyToManyField(Person, blank=True)
    created_by = models.ForeignKey(Person, on_delete=models.CASCADE, null=True, blank=True, related_name="created_by")

    @property
    def allergic_people(self) -> models.QuerySet:
        return self.party.people().filter(allergy__ingredient__in=self.ingredients.all())

    def allergens(self) -> list[str]:
        allergen_people = self.party.people().filter(allergy__ingredient__in=self.ingredients.all())
        return [i.name for i in Ingredient.objects.filter(allergy__person__in=allergen_people)]

    def assign_to(self, person: Person) -> None:
        if self.party.invite_set.filter(person=person, status__in=("Y", "M")).exists():
            self.assigned_to.add(person)
            self.save()
            return
        raise ValueError(f"{person} is not invited to {self.party}")

    @property
    def party_edition(self) -> str:
        return self.party.edition

    def __str__(self):
        base_str = f"{self.name} @ {self.party}"
        if self.assigned_to.exists():
            return f"{base_str} ({', '.join([p.get_display_name() for p in self.assigned_to.all()])})"
        return base_str

    class Meta:
        indexes = [
            models.Index(fields=["party", "category"]),
        ]


class PartyFile(models.Model):
    parties = models.ManyToManyField(Party, blank=True)
    name = models.CharField(max_length=30, db_index=True)
    file = models.FileField(upload_to="files", db_index=True)
    description = models.CharField(max_length=250, db_index=True, null=True, blank=True)

    @property
    def url(self) -> str:
        return self.file.url

    def __str__(self):
        return f"{self.file.name}"


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


class ApiClient(models.Model):
    name = models.CharField(max_length=30, db_index=True)
    api_key = models.UUIDField(primary_key=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True, db_index=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["-created_at"]
        index_together = [
            ["api_key", "active"],
        ]
