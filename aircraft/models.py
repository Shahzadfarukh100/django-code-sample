# Core
import logging

from mx.utils import is_current_mx_client

logger = logging.getLogger(__name__)
from datetime import datetime, timedelta

# Django
from django.db import models
from django.apps import apps
from django.utils import timezone

# Third-Party

# App
from tickets.models import TicketRequest


class AircraftManufacturer(models.Model):
    name = models.CharField(max_length=50, db_index=True)
    public = models.BooleanField(default = False)
    ignore = models.BooleanField(default = False)
    def __str__(self):
        return self.name

class AircraftModel(models.Model):
    manufacturer = models.ForeignKey(AircraftManufacturer, on_delete=models.PROTECT)
    name = models.CharField(max_length=50, db_index=True)
    public = models.BooleanField(default = False)
    ignore = models.BooleanField(default = False)
    twin = models.NullBooleanField(db_index=True, null=True, blank=True)

    def __str__(self):
        return self.name


class EngineManufacturer(models.Model):
    name = models.CharField(max_length=50, db_index=True)
    public = models.BooleanField(default = False)
    ignore = models.BooleanField(default = False)

    def __str__(self):
        return self.name


class EngineModel(models.Model):
    manufacturer = models.ForeignKey(EngineManufacturer, on_delete=models.PROTECT)
    name = models.CharField(max_length=50, db_index=True)
    public = models.BooleanField(default = False)
    ignore = models.BooleanField(default = False)

    def __str__(self):
        return self.name


class EngineMonitorManufacturer(models.Model):
    name = models.CharField(max_length=50, db_index=True)
    public = models.BooleanField(default = False)
    ignore = models.BooleanField(default = False)

    def __str__(self):
        return self.name


class EngineMonitorModel(models.Model):
    manufacturer = models.ForeignKey(EngineMonitorManufacturer, on_delete=models.PROTECT)
    name = models.CharField(max_length=50, db_index=True)
    public = models.BooleanField(default = False)
    ignore = models.BooleanField(default = False)

    def __str__(self):
        return self.name