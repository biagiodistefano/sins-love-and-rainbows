# Generated by Django 4.2.7 on 2023-12-19 11:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0019_alter_partyfile_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='party',
            name='name',
            field=models.CharField(db_index=True, max_length=128, unique=True),
        ),
    ]
