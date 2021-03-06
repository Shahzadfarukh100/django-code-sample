# Generated by Django 2.1.1 on 2018-09-19 06:02

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Aircraft',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('registration_no', models.CharField(blank=True, db_index=True, max_length=50, null=True)),
                ('year', models.CharField(blank=True, db_index=True, max_length=4, null=True)),
                ('serial', models.CharField(blank=True, db_index=True, max_length=50, null=True)),
                ('default', models.BooleanField(default=False)),
                ('monitor_config', models.CharField(blank=True, max_length=1024, null=True)),
                ('cylinder_count', models.CharField(blank=True, choices=[('2', '2'), ('4', '4'), ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9')], max_length=2, null=True)),
                ('remarks', models.CharField(blank=True, max_length=128, null=True)),
                ('cht_warning_temperature', models.PositiveIntegerField(blank=True, null=True)),
                ('owner_first_name', models.CharField(blank=True, max_length=50, null=True)),
                ('owner_last_name', models.CharField(blank=True, max_length=50, null=True)),
                ('owner_email', models.EmailField(blank=True, max_length=255, null=True)),
                ('analyst_notes', models.TextField(blank=True, max_length=1000, null=True)),
                ('hidden', models.BooleanField(db_index=True, default=False)),
                ('measures', models.CharField(default='US', max_length=2)),
            ],
        ),
        migrations.CreateModel(
            name='AircraftConversion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('series_name', models.CharField(max_length=50)),
                ('aircraft', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='aircraft.Aircraft')),
            ],
        ),
        migrations.CreateModel(
            name='AircraftManufacturer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=50)),
                ('public', models.BooleanField(default=False)),
                ('ignore', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='AircraftModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=50)),
                ('public', models.BooleanField(default=False)),
                ('ignore', models.BooleanField(default=False)),
                ('twin', models.NullBooleanField(db_index=True)),
                ('manufacturer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='aircraft.AircraftManufacturer')),
            ],
        ),
        migrations.CreateModel(
            name='EngineManufacturer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=50)),
                ('public', models.BooleanField(default=False)),
                ('ignore', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='EngineModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=50)),
                ('public', models.BooleanField(default=False)),
                ('ignore', models.BooleanField(default=False)),
                ('manufacturer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='aircraft.EngineManufacturer')),
            ],
        ),
        migrations.CreateModel(
            name='EngineMonitorManufacturer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=50)),
                ('public', models.BooleanField(default=False)),
                ('ignore', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='EngineMonitorModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=50)),
                ('public', models.BooleanField(default=False)),
                ('ignore', models.BooleanField(default=False)),
                ('manufacturer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='aircraft.EngineMonitorManufacturer')),
            ],
        ),
        migrations.CreateModel(
            name='UnitConversion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('from_name', models.CharField(max_length=50)),
                ('to_name', models.CharField(max_length=50)),
                ('group_name', models.CharField(max_length=50)),
                ('a_param', models.FloatField()),
                ('b_param', models.FloatField()),
            ],
        ),
        migrations.AddField(
            model_name='aircraftconversion',
            name='unitconversion',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='aircraft.UnitConversion', verbose_name='Conversion'),
        ),
        migrations.AddField(
            model_name='aircraft',
            name='aircraft_manufacturer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='aircraft.AircraftManufacturer'),
        ),
        migrations.AddField(
            model_name='aircraft',
            name='aircraft_model',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='aircraft.AircraftModel'),
        ),
        migrations.AddField(
            model_name='aircraft',
            name='conversions',
            field=models.ManyToManyField(through='aircraft.AircraftConversion', to='aircraft.UnitConversion'),
        ),
        migrations.AddField(
            model_name='aircraft',
            name='engine_manufacturer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='aircraft.EngineManufacturer'),
        ),
        migrations.AddField(
            model_name='aircraft',
            name='engine_model',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='aircraft.EngineModel'),
        ),
        migrations.AddField(
            model_name='aircraft',
            name='engine_monitor_manufacturer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='aircraft.EngineMonitorManufacturer'),
        ),
        migrations.AddField(
            model_name='aircraft',
            name='engine_monitor_model',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='aircraft.EngineMonitorModel'),
        ),
        migrations.AddField(
            model_name='aircraft',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
    ]
