# Generated by Django 3.1.7 on 2021-07-15 13:24

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0006_company_problem_owners_can_invite'),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(max_length=3000)),
                ('code', models.CharField(max_length=20)),
                ('date_from', models.DateField()),
                ('date_to', models.DateField()),
                ('problem_submission_date_from', models.DateField()),
                ('problem_submission_date_to', models.DateField()),
                ('event_image', models.ImageField(blank=True, null=True, upload_to='')),
                ('event_type', models.SmallIntegerField(choices=[(1, 'Conference'), (2, 'Workshop'), (3, 'Sprint'), (4, 'Seminar'), (5, 'Competition'), (6, 'Webinar'), (7, 'Program'), (8, 'Course'), (9, 'Other')], default=1)),
                ('internal_or_external', models.SmallIntegerField(choices=[(1, 'Internal'), (2, 'External')], default=1)),
                ('private_or_public', models.SmallIntegerField(choices=[(1, 'Private'), (2, 'Public')], default=1)),
                ('physical_or_digital', models.SmallIntegerField(choices=[(1, 'Physical'), (2, 'Digital'), (3, 'Physical and digital')], default=1)),
                ('host_has_problem_access', models.BooleanField(default=False)),
                ('host_on_boards_members', models.BooleanField(default=False)),
                ('problem_owner_on_boards_members', models.BooleanField(default=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.company')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EventOnBoardedParticipants',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='event.event')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EventHosts',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='event.event')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='event',
            name='host',
            field=models.ManyToManyField(related_name='hosts_event', through='event.EventHosts', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='event',
            name='on_boarded_participants',
            field=models.ManyToManyField(related_name='on_board_participants_event', through='event.EventOnBoardedParticipants', to=settings.AUTH_USER_MODEL),
        ),
    ]
