# Core
import logging
logger = logging.getLogger(__name__)

# Django
from django.db import models

# Third-Party

# App


SUMMARY_CHECKBOXES = [(0, 'Select a value'), ('Satisfactory', 'Satisfactory'), ('Caution', 'Caution'), ('Alert', 'Alert'), ('N/A', 'N/A')]

class FlightReport(models.Model):
    ticket = models.ForeignKey("tickets.TicketRequest", null=True, blank=True, on_delete=models.PROTECT)
    engine = models.IntegerField(verbose_name='Engine') # 0 Single, 1 Left, 2 Right
    sister_report = models.ForeignKey("FlightReport", null=True, blank=True, on_delete=models.PROTECT)

    created_on = models.DateTimeField(db_index=True, blank=True, null=True)
    last_update_on = models.DateTimeField(db_index=True, blank=True, null=True)

    client_comments = models.TextField(max_length=2000, default="", blank=True, verbose_name='Client Comments')

    flight = models.ForeignKey("flights.Flight", on_delete=models.PROTECT)

    gami1 = models.TextField(max_length=1000, default="", blank=True, verbose_name='Sweep #1')
    gami2 = models.TextField(max_length=1000, default="", blank=True, verbose_name='Sweep #2')
    gami3 = models.TextField(max_length=1000, default="", blank=True, verbose_name='Sweep #3')
    gami4 = models.TextField(max_length=1000, default="", blank=True, verbose_name='Observations')
    gami_summary = models.CharField(max_length= 30, default="", blank=True, verbose_name='GAMI Lean Test')

    ignition1 = models.CharField(max_length=100, default="", blank=True, verbose_name='Non-firing plug(s)')
    ignition2 = models.CharField(max_length=100, default="", blank=True, verbose_name='Marginal plug(s)')
    ignition3 = models.CharField(max_length=100, default="", blank=True, verbose_name='Split mag timing')
    ignition4 = models.CharField(max_length=100, default="", blank=True, verbose_name='Add\'l observations')
    ignition_summary = models.CharField(max_length= 30, default="", blank=True, verbose_name='Ignition')

    power1 = models.CharField(max_length=100, default="", blank=True, verbose_name='Max power FF')
    power2 = models.CharField(max_length=100, default="", blank=True, verbose_name='Max power RPM')
    power3 = models.CharField(max_length=100, default="", blank=True, verbose_name='Maximum MAP')
    power4 = models.CharField(max_length=100, default="", blank=True, verbose_name='Add\'l observations')
    power_summary = models.CharField(max_length= 30, default="", blank=True, verbose_name='Max Power')

    temperatures1 = models.CharField(max_length=100, default="", blank=True, verbose_name='CHTs')
    temperatures2 = models.CharField(max_length=100, default="", blank=True, verbose_name='EGTs')
    temperatures3 = models.CharField(max_length=100, default="", blank=True, verbose_name='TIT(s)')
    temperatures4 = models.CharField(max_length=100, default="", blank=True, verbose_name='Add\'l observations')
    temperatures_summary = models.CharField(max_length= 30, default="", blank=True, verbose_name='Temperatures')

    monitor1 = models.CharField(max_length=100, default="", blank=True, verbose_name='Inoperative sensors')
    monitor2 = models.CharField(max_length=100, default="", blank=True, verbose_name='Anomalous channels')
    monitor3 = models.CharField(max_length=100, default="", blank=True, verbose_name='Noisy channels')
    monitor4 = models.CharField(max_length=100, default="", blank=True, verbose_name='Add\'l observations')
    monitor_summary = models.CharField(max_length= 30, default="", blank=True, verbose_name='Engine Monitor')

    powerplant1 = models.CharField(max_length=100, default="", blank=True, verbose_name='Power')
    powerplant2 = models.CharField(max_length=100, default="", blank=True, verbose_name='Mixture')
    powerplant3 = models.CharField(max_length=100, default="", blank=True, verbose_name='Test Profile(s)')
    powerplant4 = models.CharField(max_length=100, default="", blank=True, verbose_name='Add\'l observations')
    powerplant_summary = models.CharField(max_length= 30, default="", blank=True, verbose_name='Powerplant Mgt')

    electrical1 = models.CharField(max_length=100, default="", blank=True, verbose_name='Primary sys')
    electrical2 = models.CharField(max_length=100, default="", blank=True, verbose_name='Secondary sys')
    electrical3 = models.CharField(max_length=100, default="", blank=True, verbose_name='Other sensors')
    electrical4 = models.CharField(max_length=100, default="", blank=True, verbose_name='Add\'l observations')
    electrical_summary = models.CharField(max_length= 30, default="", blank=True, verbose_name='Electrical')

    findings = models.TextField(max_length=2000, default="", blank=True, verbose_name='Summary of Findings')
    recommendations = models.TextField(max_length=2000, default="", blank=True, verbose_name='Recommendations')
    additional = models.TextField(max_length=10000, default="", blank=True, verbose_name='Additional Remarks')

    @staticmethod
    def exists(field):
        return field is not None and field != "" and field != '0'

    def not_empty(self):
        return self.exists(self.findings) or self.exists(self.recommendations) or self.exists(self.additional) or self.exists(self.gami_summary) or self.exists(self.gami1) or self.exists(self.gami2) or self.exists(self.gami3) or self.exists(self.gami4) or self.exists(self.ignition_summary)or self.exists(self.ignition1) or self.exists(self.ignition2) or self.exists(self.ignition3) or self.exists(self.ignition4) or self.exists(self.power_summary) or self.exists(self.power1) or self.exists(self.power2) or self.exists(self.power3) or self.exists(self.power4) or self.exists(self.temperatures_summary) or self.exists(self.temperatures1) or self.exists(self.temperatures2) or self.exists(self.temperatures3) or self.exists(self.temperatures4) or self.exists(self.electrical_summary) or self.exists(self.electrical1) or self.exists(self.electrical2) or self.exists(self.electrical3) or self.exists(self.electrical4) or self.exists(self.monitor_summary) or self.exists(self.monitor1) or self.exists(self.monitor2) or self.exists(self.monitor3) or self.exists(self.monitor4) or self.exists(self.powerplant_summary) or self.exists(self.powerplant1) or self.exists(self.powerplant2) or self.exists(self.powerplant3) or self.exists(self.powerplant4)
