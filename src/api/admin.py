"""Register all models in the admin site."""

from django.apps import apps
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
# from django import forms

from .models import Party, Invite, Person, Allergy, Item, PartyFile


class AllergyInline(admin.TabularInline):
    model = Allergy.people.through


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):

    inlines = [AllergyInline]

    list_display = ('first_name', 'in_broadcast', 'from_abroad', 'allergies_list')

    @admin.display(description='Allergies')
    def allergies_list(self, obj: Person) -> str:
        return ", ".join(obj.allergy_set.values_list("ingredient__name", flat=True))


class PartyFileInline(admin.TabularInline):
    model = PartyFile
    classes = ['collapse']


class InviteInline(admin.TabularInline):
    model = Invite
    # form = InviteForm
    classes = ['collapse']


class ItemInline(admin.TabularInline):
    model = Item
    classes = ['collapse']
    fields = ('category', 'name', 'quantity', 'description', 'ingredients', 'assigned_to')


@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    inlines = [InviteInline, ItemInline, PartyFileInline]

    list_display = ('name', 'date_and_time', 'yes_count', 'no_count', 'maybe_count', 'party_url')

    @admin.display(description='Yes')
    def yes_count(self, obj: Party) -> int:
        return obj.yes_count()

    @admin.display(description='No')
    def no_count(self, obj: Party) -> int:
        return obj.no_count()

    @admin.display(description='Maybe')
    def maybe_count(self, obj: Party) -> int:
        return obj.maybe_count()

    @admin.display(description='Allergies')
    def allergies_list(self, obj: Party) -> str:
        return ", ".join(obj.allergy_list())

    @admin.display(description='Url')
    def party_url(self, obj: Party) -> str:
        url = reverse("party", kwargs={"edition": obj.edition})
        return format_html('<a href="{}">{}</a>', url, obj.name)

    fieldsets = (
        (None, {
            'fields': ('name', "edition", "date_and_time", "location", "description"),
        }),
        ('Response Counts', {
            'fields': ('yes_count', 'no_count', 'maybe_count'),
            # 'classes': ('collapse',),
        }),
        ('Allergies', {
            'fields': ('allergies_list',),
            # 'classes': ('collapse',),
        }),
    )

    readonly_fields = ('yes_count', 'no_count', 'maybe_count', 'allergies_list')


post_models = apps.get_app_config("api").get_models()

for model in post_models:
    try:
        admin.site.register(model)
    except admin.sites.AlreadyRegistered:
        pass
