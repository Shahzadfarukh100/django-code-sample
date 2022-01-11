# Core
import time

# Django
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.urls import reverse, reverse_lazy
from django.conf import settings
from django.utils import timezone
from django.views.generic import FormView

# Third-party

# App
from mx.utils import get_all_mx_aircraft_and_owners
from tickets.models import TicketRequest, TicketRequestHistory, TicketRequestReportingTags, TicketCategoryReportingTag

from analyst_tickets.emailutils import notify_ticket

from analyst_tickets.models import TimeSheetEntry
from analyst_tickets.utils import stop_timesheet_entry, submit_timesheet_and_clear
from flights.models import (
    Flight,
)

from account.models import Subscription, User
from main.helpspot import ticket_for_user
from files.models import (
    EngineDataFile,
)
from aircraft.models import Aircraft
from analyst.models import FlightReport, FlightReportClipboadEntry
from analyst.forms import (
    PostReportAndUserForm,
    FlightForm,
    PostReportForm,
    FlightFormMx,
    ClientNotesForm,
    FlightReportSearchForm
)
from analyst.reports import PdfReport

# TODO: Suspect imports - rethink location of code
from aircraft.forms import AnalystNotesForm
from tickets.utils import (send_report,
                           send_shop_report_to_owner,
                           get_ticket_body,
                           get_ticket_history,
                           attach_file,
                           get_ticket_time)


@login_required
@permission_required('global_permission.view_user_data', login_url=reverse_lazy('permissions-error'))
def analyst_file_search(request):
    if request.is_ajax():
        q = request.POST.get('filename', '')
        if q:
            edfs = EngineDataFile.objects.prefetch_related('aircraft', 'user').filter(name__icontains=q)
            return render(request, 'analyst/_file-list.html', { 'edfs': edfs })
    return render(request, 'analyst/file-search.html', {})


@login_required
def download_edf(request, edf_id):
    if request.user.has_perm('global_permission.download_flight_data'):
        failed_upload = EngineDataFile.all_objects.get(id=edf_id)
        return HttpResponseRedirect(failed_upload.get_url())
    else:
        try:
            failed_upload = EngineDataFile.all_objects.get(id=edf_id, user_id=request.user.id)
            return HttpResponseRedirect(failed_upload.get_url())
        except:
            return render(request, 'skeletons/basic.html', { 'title': "Error", 'text': 'File does not exist or download not allowed.' })

@login_required
def download_raw_data(request, flight_id):
    if request.user.has_perm('global_permission.download_flight_data'):
        flight = Flight.objects.get(id=flight_id)
        return HttpResponseRedirect(flight.get_url())
    else:
        return render(request, 'skeletons/basic.html', { 'title': "Error", 'text': 'File does not exist or download not allowed.' })


@login_required
@permission_required('global_permission.manage_sa_reports', login_url=reverse_lazy('permissions-error'))
def generate_report(request, ticket_id, flight_id):

    # Grab the ticket and related context
    try:
        ticket = TicketRequest.objects.get(id=ticket_id, trash=0)
    except TicketRequest.DoesNotExist:
        return render(request, 'tickets/ticket_not_public.html')

    user_id = ticket.user_id
    _, history, _ = get_ticket_history(ticket_id)

    # Check that there are no existing reports for this ticket and flight
    existing_reports = FlightReport.objects.filter(ticket_id=ticket.id, flight_id=flight_id)
    if len(existing_reports) > 0:
        return render(request, 'skeletons/basic.html',
                      {'title': "Error", 'text': 'A report already exists for this ticket/flight combination.'})


    context = dict(kind="SavvyAnalysis", ticket_id=ticket_id)
    context['ticket'] = ticket
    context['aircraft'] = Aircraft.objects.get(id=ticket.aircraft_id)
    if user_id is None:
        user_id = context['aircraft'].user_id
    context['user_id'] = user_id if user_id is not None else 0
    context['ticket_user'] = User.objects.get(id=user_id)
    context['report_date'] = timezone.now()
    context['analyst_notes_form'] = AnalystNotesForm(instance=context['aircraft'])
    context['client_comments'] = history[-1].note.replace('\r', '<br/>')
    context['flight_id'] = flight_id
    context['report_id'] = None
    context['return_url'] = reverse('analyst_ticket', args=[ticket_id])
    context['copy_report'] = False

    # Get the report to paste, a mismatch (single/twin) or nothing
    try:
        paste_report_instance = FlightReportClipboadEntry.objects.get(user=request.user).report
        source_is_twin = paste_report_instance.flight.aircraft.aircraft_model.twin
        target_is_twin = context['aircraft'].aircraft_model.twin
        if source_is_twin == target_is_twin:
            context['paste_report'] = reverse('paste_report', args=[ paste_report_instance.id, ticket_id, flight_id ])
            context['paste_report_data'] = "Copying from ticket #{}, report #{}, flight #{}".format(paste_report_instance.ticket_id, paste_report_instance.id, paste_report_instance.flight_id)
        else:
            context['paste_report'] = 'error'
            if source_is_twin:
                context['paste_report_error'] = "Cannot paste twin engine report into single."
            else:
                context['paste_report_error'] = "Cannot paste single engine report into twin."

    except FlightReportClipboadEntry.DoesNotExist:
        context['paste_report'] = None

    relevant_flight = Flight.objects.get(aircraft__user_id=user_id,
                                         aircraft=context['aircraft'], id=flight_id)

    if request.method == "GET":
        # Get hold of the relevant flight, and existing reports (if any)
        context['flight_forms'] = []

        if not context['aircraft'].aircraft_model.twin:
            context['flight_forms'].append(FlightForm(prefix=str(0),
                                                      initial={'engine': 0, 'flight': relevant_flight,
                                                               'ticket': ticket }))
        else:
            context['flight_forms'].append(FlightForm(prefix=str(1),
                                                      initial={'engine': 1, 'flight': relevant_flight,
                                                               'ticket': ticket }))
            context['flight_forms'].append(FlightForm(prefix=str(2),
                                                      initial={'engine': 2, 'flight': relevant_flight,
                                                               'ticket': ticket }))



    elif request.method == "POST":

        if not context['aircraft'].aircraft_model.twin:
            form = FlightForm(request.POST, prefix='0')

            if form.is_valid():
                new_instance = form.save()
                if new_instance.created_on is None:
                    new_instance.created_on = timezone.now()
                    new_instance.last_update_on = timezone.now()
                    new_instance.save()

                context['flight_forms'] = [form]
                context['pdf_download'] = reverse('download_report', args=[ticket.id, flight_id, 1])
                context['pdf_preview'] = reverse('preview_report', args=[ticket.id, flight_id])
                return HttpResponseRedirect(reverse('edit_report', args=[new_instance.id]))
            else:
                context['flight_forms'] = [form]

        else:
            left_form = FlightForm(request.POST, prefix='1')
            right_form = FlightForm(request.POST, prefix='2')

            context['flight_forms'] = [left_form, right_form]
            if left_form.is_valid() and right_form.is_valid():
                new_left = left_form.save()
                new_right = right_form.save()

                if new_left.created_on is None:
                    new_left.created_on = timezone.now()
                new_left.last_update_on = timezone.now()
                new_left.save()

                if new_right.created_on is None:
                    new_right.created_on = timezone.now()
                new_right.last_update_on = timezone.now()
                new_right.sister_report = new_left
                new_right.save()

                # Gotta do this after we save the right engine
                new_left.sister_report = new_right
                new_left.save()


                context['pdf_download'] = reverse('download_report', args=[ticket.id, flight_id, 1])
                context['pdf_preview'] = reverse('preview_report', args=[ticket.id, flight_id])
                return HttpResponseRedirect(reverse('edit_report', args=[new_left.id]))


        return HttpResponseRedirect(reverse('edit_report', []))

    return render(request, 'analyst/report-form.html', context)

