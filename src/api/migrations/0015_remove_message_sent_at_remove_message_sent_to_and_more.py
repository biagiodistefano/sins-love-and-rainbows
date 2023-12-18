# Generated by Django 4.2.7 on 2023-12-18 11:58

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0014_party_private'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='message',
            name='sent_at',
        ),
        migrations.RemoveField(
            model_name='message',
            name='sent_to',
        ),
        migrations.CreateModel(
            name='MessageLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sent_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('sent', models.BooleanField(db_index=True, default=False)),
                ('sent_via', models.CharField(blank=True, choices=[('W', 'WhatsApp'), ('S', 'SMS'), ('E', 'Email'), ('T', 'Telegram')], db_index=True, max_length=30, null=True)),
                ('sid', models.CharField(blank=True, max_length=34, null=True)),
                ('error', models.BooleanField(db_index=True, default=False)),
                ('error_message', models.TextField(blank=True, null=True)),
                ('message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.message')),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'message logs',
            },
        ),
    ]
