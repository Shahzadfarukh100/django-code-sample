# Generated by Django 3.1.7 on 2021-08-23 10:27

from django.db import migrations
import django_quill.fields


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0009_auto_20210818_0623'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='description',
            field=django_quill.fields.QuillField(max_length=3000),
        ),
    ]
