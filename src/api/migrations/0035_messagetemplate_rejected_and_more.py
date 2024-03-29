# Generated by Django 4.2.7 on 2024-02-02 11:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0034_messagetemplate_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='messagetemplate',
            name='rejected',
            field=models.BooleanField(db_index=True, default=False, editable=False),
        ),
        migrations.AddField(
            model_name='messagetemplate',
            name='rejection_reason',
            field=models.TextField(blank=True, null=True),
        ),
    ]
