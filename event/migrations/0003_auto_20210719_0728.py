# Generated by Django 3.1.7 on 2021-07-19 07:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0002_event_one_liner_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='code',
            field=models.CharField(max_length=20, unique=True),
        ),
    ]
