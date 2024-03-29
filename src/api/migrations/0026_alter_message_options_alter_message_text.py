# Generated by Django 4.2.7 on 2024-01-09 10:38

from django.db import migrations
import markdownfield.models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0025_messagesent_alter_personallinksent_index_together_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='message',
            options={'ordering': ['-party__date_and_time', '-due_at']},
        ),
        migrations.AlterField(
            model_name='message',
            name='text',
            field=markdownfield.models.MarkdownField(blank=True, null=True, rendered_field='text_rendered'),
        ),
    ]
