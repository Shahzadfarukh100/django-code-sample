# Core
import json
from datetime import datetime

# Django
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.forms import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Sum
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView
from django.utils.translation import ugettext as _
from django.utils import timezone

# Third-party
from dal import autocomplete

# App
from account.models import (
    AnalysisPack,
    APIToken,
)

from flights.models import (
    Flight,
)

from aircraft.forms import (
    AircraftCompleteForm,
    AircraftEditForm,
    AircraftForm,
    UBG16Form,
    MGLForm,
    ConversionForm,
    AnalystNotesForm,
)

from aircraft.models import (
    AircraftManufacturer,
    AircraftModel,
    EngineManufacturer,
    EngineModel,
    EngineMonitorManufacturer,
    EngineMonitorModel,
    Aircraft,
    AircraftConversion,
)
from mx.models import MxAircraft
from mx.utils import get_aircraft_from_mx_db


class AircraftListView(ListView):
    template_name = 'aircraft/list.html'
    context_object_name = 'aircraft'

    def get_queryset(self):
        return Aircraft.objects.filter(user=self.request.user, hidden=False).order_by('registration_no')

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(AircraftListView, self).get_context_data(**kwargs)
        # Add in a QuerySet of all the books
        packs = AnalysisPack.objects.filter(user=self.request.user)
        if len(packs) == 0:
            context['no_packs'] = True
        else:
            valid_packs = AnalysisPack.objects.filter(user=self.request.user, expiration_date__gte=timezone.now())
            if len(valid_packs) == 0:
                context['remaining_analyses'] = "no"
            else:
                context['remaining_analyses'] = valid_packs.aggregate(Sum('remaining_incidents'))[
                    'remaining_incidents__sum']

        return context



@login_required
def aircraft_list_conversions(request, aircraft_id):
    if request.method != 'GET':
        return HttpResponse('Not supported')

    try:
        aircraft = Aircraft.objects.get(id=aircraft_id, user_id=request.user.id, hidden=False)
    except Aircraft.DoesNotExist:
        return render(request, 'skeletons/basic.html', {'title': "Error", 'text': 'Aircraft does not exist.'})

    try:
        most_recent_flights = Flight.objects.filter(aircraft=aircraft).order_by('id').reverse()
        if len(most_recent_flights) >= 5:
            most_recent_flights = most_recent_flights[0:5]

        most_recent_flight_series = []
        for flight in most_recent_flights:
            data = json.loads(flight.data())
            most_recent_flight_series += data['series_data'].keys()
        most_recent_flight_series = list(set(most_recent_flight_series))

        most_recent_flight_series_filtered = []
        for serie in most_recent_flight_series:
            if 'EGT' not in serie.upper() and 'CHT' not in serie.upper():
                most_recent_flight_series_filtered.append(serie)

        most_recent_flight_series_filtered = sorted(most_recent_flight_series_filtered)
        most_recent_flight_series_filtered = ['EGT (all cylinders)', 'CHT (all cylinders)'] + most_recent_flight_series_filtered

    except:
        most_recent_flight_series_filtered = None
    conversions = aircraft.aircraftconversion_set.all()

    return render(request, 'aircraft/edit_measures.html',
                  {'aircraft': aircraft, 'conversions': conversions, 'form': ConversionForm(aircraft_id=aircraft_id),
                   'most_recent_flight_series': most_recent_flight_series_filtered})


@login_required
def aircraft_add_conversion(request, aircraft_id):
    if request.method != 'POST':
        return HttpResponse('Not supported')

    try:
        aircraft = Aircraft.objects.get(id=aircraft_id, user_id=request.user.id, hidden=False)
    except Aircraft.DoesNotExist:
        return render(request, 'skeletons/basic.html', {'title': "Error", 'text': 'Aircraft does not exist.'})

    form = ConversionForm(request.POST, aircraft_id=aircraft_id)
    if form.is_valid():
        conversion = AircraftConversion(
            aircraft=aircraft,
            unitconversion=form.cleaned_data['unitconversion'],
            series_name=form.cleaned_data['series_name'],
        )
        conversion.save()
        return HttpResponseRedirect(reverse('aircraft_list_conversions', args=[aircraft_id]))
    else:
        return HttpResponse('Invalid form')


@login_required
def aircraft_delete(request, aircraft_id):
    try:
        aircraft = Aircraft.objects.get(id=aircraft_id, user_id=request.user.id, hidden=False)
    except Aircraft.DoesNotExist:
        return render(request, 'skeletons/basic.html', {'title': "Error", 'text': 'Aircraft does not exist.'})

    if request.method != 'POST':
        return HttpResponse('Unsupported')

    if aircraft.current_subscription() is not None:
        return HttpResponse('Cannot delete an aircraft with an active subscription.')
    aircraft.delete()
    return HttpResponse("ok")


@login_required
def complete_profile(request, aircraft_id, kind):
    # Kind will be "pack" or "pro".
    # Packs can edit registration and aircraft make/model

    aircraft = Aircraft.objects.get(user_id=request.user.id, hidden=False, id=aircraft_id)

    if request.method == 'GET':
        form = AircraftCompleteForm(initial=model_to_dict(aircraft),
                                    kind=kind,
                                    aircraft_id=aircraft_id)
    elif request.method == 'POST':
        form = AircraftCompleteForm(request.POST, kind=kind, aircraft_id=aircraft_id)
        if form.is_valid():
            aircraft.year = form.cleaned_data['year']
            aircraft.serial = form.cleaned_data['serial']
            aircraft.cht_warning_temperature = form.cleaned_data['cht_warning_temperature']
            aircraft.cylinder_count = form.cleaned_data['cylinder_count']
            aircraft.remarks = form.cleaned_data['remarks']

            if kind == "pack":
                aircraft.registration_no = form.cleaned_data['registration_no']

                if form.cleaned_data['aircraft_manufacturer'] != "":
                    aircraft.aircraft_manufacturer = form.cleaned_data['aircraft_manufacturer']
                if form.cleaned_data['aircraft_model'] != "":
                    aircraft.aircraft_model = form.cleaned_data['aircraft_model']

            if form.cleaned_data['engine_manufacturer'] != "":
                aircraft.engine_manufacturer = form.cleaned_data['engine_manufacturer']
            if form.cleaned_data['engine_model'] != "":
                aircraft.engine_model = form.cleaned_data['engine_model']

            if form.cleaned_data['engine_monitor_manufacturer'] != "":
                aircraft.engine_monitor_manufacturer = form.cleaned_data['engine_monitor_manufacturer']
            if form.cleaned_data['engine_monitor_model'] != "":
                aircraft.engine_monitor_model = form.cleaned_data['engine_monitor_model']

            aircraft.save()

            return HttpResponseRedirect(reverse('files_upload'))
    else:
        return HttpResponse('Not supported')

    return render(request, 'aircraft/complete.html',
                  { 'form': form,
                    'pro_form': kind == "pro",
                    'aircraft_id': aircraft.id,
                    'aircraft': aircraft,
                   })
