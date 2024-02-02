"""Register all models in the admin site."""

from django.apps import apps
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Allergy, Invite, Item, Message, MessageSent, MessageTemplate, Party, PartyFile, Person


# from django import forms


class AllergyInline(admin.TabularInline):
    model = Allergy


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    readonly_fields = ("id",)

    inlines = [AllergyInline]

    list_display = ("first_name", "in_broadcast", "from_abroad", "whatsapp_message", "allergies_list")

    @admin.display(description="Message")
    def whatsapp_message(self, obj: Person) -> str:
        if whatsapp_message_url := obj.whatsapp_message_url():
            return format_html(
                f'<a target="_blank" href="{whatsapp_message_url}">Message on WhatsApp</a>',
            )
        return ""

    @admin.display(description="Allergies")
    def allergies_list(self, obj: Person) -> str:
        return ", ".join(allergy.name for allergy in obj.allergies.all())


class PartyFileInline(admin.TabularInline):
    model = PartyFile.parties.through
    classes = ["collapse"]


class InviteInline(admin.TabularInline):
    model = Invite
    classes = ["collapse"]


class ItemInline(admin.TabularInline):
    model = Item
    classes = ["collapse"]
    fields = ("category", "name", "quantity", "description", "ingredients", "assigned_to")


@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    readonly_fields = (
        "status",
        "sid",
        "rejection_reason",
    )

    list_display = (
        "title",
        "status",
        "is_default_party_message",
    )


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_filter = (
        "party",
        "autosend",
        "draft",
    )
    readonly_fields = ("id",)
    list_display = (
        "title",
        "party",
        "due_at",
    )


@admin.register(Invite)
class InviteAdmin(admin.ModelAdmin):
    list_filter = (
        "party",
        "status",
    )
    readonly_fields = ("id",)


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_filter = (
        "party",
        "category",
        "assigned_to",
    )
    readonly_fields = ("id",)


@admin.register(MessageSent)
class MessageSentAdmin(admin.ModelAdmin):
    list_filter = (
        "party",
        "message",
        "sent",
        "error",
        "status",
        "person",
    )
    readonly_fields = ("sent_at",)
    list_display = ("party", "title", "person", "status", "sent_at")

    def title(self, obj: MessageSent) -> str:
        return obj.message.title


@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    inlines = [InviteInline, ItemInline, PartyFileInline]

    list_display = ("name", "date_and_time", "yes_count", "no_count", "maybe_count", "party_url")

    @admin.display(description="Total invites")
    def total_invites(self, obj: Party) -> int:
        return obj.invite_set.count()

    @admin.display(description="Yes")
    def yes_count(self, obj: Party) -> int:
        return obj.yes_count()

    @admin.display(description="No")
    def no_count(self, obj: Party) -> int:
        return obj.no_count()

    @admin.display(description="Maybe")
    def maybe_count(self, obj: Party) -> int:
        return obj.maybe_count()

    @admin.display(description="Allergies")
    def allergies_list(self, obj: Party) -> str:
        return ", ".join(obj.allergy_list())

    @admin.display(description="Url")
    def party_url(self, obj: Party) -> str:
        url = reverse("party", kwargs={"edition": obj.edition})
        return format_html('<a href="{}">{}</a>', url, obj.name)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "edition",
                    "date_and_time",
                    "location",
                    "max_people",
                    "closed",
                    "private",
                    "description",
                ),
            },
        ),
        (
            "Response Counts",
            {
                "fields": ("total_invites", "yes_count", "no_count", "maybe_count"),
                # 'classes': ('collapse',),
            },
        ),
        (
            "Allergies",
            {
                "fields": ("allergies_list",),
                # 'classes': ('collapse',),
            },
        ),
    )

    readonly_fields = ("id", "total_invites", "yes_count", "no_count", "maybe_count", "allergies_list")


post_models = apps.get_app_config("api").get_models()

for model in post_models:
    try:
        admin.site.register(model)
    except admin.sites.AlreadyRegistered:
        pass
