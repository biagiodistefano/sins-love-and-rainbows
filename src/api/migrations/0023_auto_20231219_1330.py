# Generated by Django 4.2.7 on 2023-12-19 13:30

from django.db import migrations
from ..models import PhoneNumberField


def sanitize_phone_numbers(apps, schema_editor):
    Person = apps.get_model('api', 'Person')
    for obj in Person.objects.all():
        if obj.phone_number is None:
            continue
        obj.phone_number = PhoneNumberField.validate_phone_number(obj.phone_number)
        obj.save()


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0022_alter_preferences_options_alter_person_phone_number'),
    ]

    operations = [
        migrations.RunPython(sanitize_phone_numbers),
    ]