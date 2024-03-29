# Generated by Django 4.2.7 on 2023-12-09 15:06

import api.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0010_ingredient_allergic_people_party_max_people_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='description',
            field=api.models.StrippedCharField(blank=True, db_index=True, max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='item',
            name='name',
            field=api.models.StrippedCharField(db_index=True, max_length=120),
        ),
        migrations.AlterField(
            model_name='item',
            name='quantity',
            field=api.models.StrippedCharField(blank=True, db_index=True, max_length=30, null=True),
        ),
    ]
