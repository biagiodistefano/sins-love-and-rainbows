# Generated by Django 4.2.7 on 2023-12-19 11:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0017_personallinksent_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='partyfile',
            name='name',
            field=models.CharField(db_index=True, max_length=128),
        ),
    ]