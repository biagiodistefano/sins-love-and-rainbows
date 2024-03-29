# Generated by Django 4.2.7 on 2023-12-02 15:58

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_remove_externallink_party_remove_partyfile_party_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ApiClient',
            fields=[
                ('name', models.CharField(db_index=True, max_length=30)),
                ('api_key', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('active', models.BooleanField(db_index=True, default=True)),
            ],
        ),
    ]
