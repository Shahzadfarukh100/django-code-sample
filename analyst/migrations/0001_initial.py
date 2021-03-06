# Generated by Django 2.1.1 on 2018-09-19 06:02

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('tickets', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('flights', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FlightReport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('engine', models.IntegerField(verbose_name='Engine')),
                ('created_on', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('last_update_on', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('client_comments', models.TextField(blank=True, default='', max_length=2000, verbose_name='Client Comments')),
                ('gami1', models.TextField(blank=True, default='', max_length=1000, verbose_name='Sweep #1')),
                ('gami2', models.TextField(blank=True, default='', max_length=1000, verbose_name='Sweep #2')),
                ('gami3', models.TextField(blank=True, default='', max_length=1000, verbose_name='Sweep #3')),
                ('gami4', models.TextField(blank=True, default='', max_length=1000, verbose_name='Observations')),
                ('gami_summary', models.CharField(blank=True, default='', max_length=30, verbose_name='GAMI Lean Test')),
                ('ignition1', models.CharField(blank=True, default='', max_length=100, verbose_name='Non-firing plug(s)')),
                ('ignition2', models.CharField(blank=True, default='', max_length=100, verbose_name='Marginal plug(s)')),
                ('ignition3', models.CharField(blank=True, default='', max_length=100, verbose_name='Split mag timing')),
                ('ignition4', models.CharField(blank=True, default='', max_length=100, verbose_name="Add'l observations")),
                ('ignition_summary', models.CharField(blank=True, default='', max_length=30, verbose_name='Ignition')),
                ('power1', models.CharField(blank=True, default='', max_length=100, verbose_name='Max power FF')),
                ('power2', models.CharField(blank=True, default='', max_length=100, verbose_name='Max power RPM')),
                ('power3', models.CharField(blank=True, default='', max_length=100, verbose_name='Maximum MAP')),
                ('power4', models.CharField(blank=True, default='', max_length=100, verbose_name="Add'l observations")),
                ('power_summary', models.CharField(blank=True, default='', max_length=30, verbose_name='Max Power')),
                ('temperatures1', models.CharField(blank=True, default='', max_length=100, verbose_name='CHTs')),
                ('temperatures2', models.CharField(blank=True, default='', max_length=100, verbose_name='EGTs')),
                ('temperatures3', models.CharField(blank=True, default='', max_length=100, verbose_name='TIT(s)')),
                ('temperatures4', models.CharField(blank=True, default='', max_length=100, verbose_name="Add'l observations")),
                ('temperatures_summary', models.CharField(blank=True, default='', max_length=30, verbose_name='Temperatures')),
                ('monitor1', models.CharField(blank=True, default='', max_length=100, verbose_name='Inoperative sensors')),
                ('monitor2', models.CharField(blank=True, default='', max_length=100, verbose_name='Anomalous channels')),
                ('monitor3', models.CharField(blank=True, default='', max_length=100, verbose_name='Noisy channels')),
                ('monitor4', models.CharField(blank=True, default='', max_length=100, verbose_name="Add'l observations")),
                ('monitor_summary', models.CharField(blank=True, default='', max_length=30, verbose_name='Engine Monitor')),
                ('powerplant1', models.CharField(blank=True, default='', max_length=100, verbose_name='Power')),
                ('powerplant2', models.CharField(blank=True, default='', max_length=100, verbose_name='Mixture')),
                ('powerplant3', models.CharField(blank=True, default='', max_length=100, verbose_name='Test Profile(s)')),
                ('powerplant4', models.CharField(blank=True, default='', max_length=100, verbose_name="Add'l observations")),
                ('powerplant_summary', models.CharField(blank=True, default='', max_length=30, verbose_name='Powerplant Mgt')),
                ('electrical1', models.CharField(blank=True, default='', max_length=100, verbose_name='Primary sys')),
                ('electrical2', models.CharField(blank=True, default='', max_length=100, verbose_name='Secondary sys')),
                ('electrical3', models.CharField(blank=True, default='', max_length=100, verbose_name='Other sensors')),
                ('electrical4', models.CharField(blank=True, default='', max_length=100, verbose_name="Add'l observations")),
                ('electrical_summary', models.CharField(blank=True, default='', max_length=30, verbose_name='Electrical')),
                ('findings', models.TextField(blank=True, default='', max_length=2000, verbose_name='Summary of Findings')),
                ('recommendations', models.TextField(blank=True, default='', max_length=2000, verbose_name='Recommendations')),
                ('additional', models.TextField(blank=True, default='', max_length=10000, verbose_name='Additional Remarks')),
                ('flight', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='flights.Flight')),
                ('sister_report', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='analyst.FlightReport')),
                ('ticket', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='tickets.TicketRequest')),
            ],
        ),
        migrations.CreateModel(
            name='FlightReportClipboadEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('report', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='analyst.FlightReport')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ReportCardData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=30)),
                ('int_value', models.IntegerField(default=None, null=True)),
                ('float_value', models.FloatField(default=None, null=True)),
                ('char_value', models.CharField(default=None, max_length=30, null=True)),
                ('flight', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='flights.Flight')),
            ],
        ),
        migrations.CreateModel(
            name='TicketLastViewed',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated', models.DateTimeField()),
                ('ticket', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tickets.TicketRequest')),
                ('viewer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='reportcarddata',
            unique_together={('flight', 'name')},
        ),
    ]
