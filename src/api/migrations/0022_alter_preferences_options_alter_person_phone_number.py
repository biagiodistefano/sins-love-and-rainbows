# Generated by Django 4.2.7 on 2023-12-19 13:29

import api.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0021_preferences'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='preferences',
            options={'ordering': ['person__first_name', 'person__last_name'], 'verbose_name_plural': 'preferences'},
        ),
        migrations.AlterField(
            model_name='person',
            name='phone_number',
            field=api.models.PhoneNumberField(blank=True, db_index=True, max_length=32, null=True),
        ),
    ]
