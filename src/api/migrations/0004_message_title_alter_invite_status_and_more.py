# Generated by Django 4.2.7 on 2023-12-01 13:02

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_alter_person_password'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='title',
            field=models.CharField(blank=True, db_index=True, max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='invite',
            name='status',
            field=models.CharField(blank=True, choices=[(None, 'No response'), ('Y', 'Yes'), ('N', 'No'), ('M', 'Maybe')], db_index=True, default=None, max_length=1, null=True),
        ),
        migrations.AlterField(
            model_name='message',
            name='sent_to',
            field=models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL),
        ),
    ]