# Generated by Django 3.1.7 on 2021-08-05 11:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0006_auto_20210728_0756'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='private_or_public',
            field=models.SmallIntegerField(choices=[(1, 'Private'), (2, 'Public')], null=True),
        ),
    ]
