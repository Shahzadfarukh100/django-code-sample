# Generated by Django 3.1.7 on 2021-07-16 10:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='one_liner_description',
            field=models.CharField(default='', max_length=200),
            preserve_default=False,
        ),
    ]
