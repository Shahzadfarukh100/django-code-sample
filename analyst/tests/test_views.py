from datetime import timedelta
import json

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.http import HttpResponse
from model_mommy import mommy
from mock import patch

from analyst.views import get_matching_report
from analyst.models import FlightReport, FlightReportClipboadEntry
from files.models import EngineDataFile
from flights.models import Flight
from aircraft.models import (AircraftModel, Aircraft, AircraftManufacturer, EngineMonitorModel,
                             EngineMonitorManufacturer, EngineModel, EngineManufacturer)
from tickets.models import TicketRequest, TicketRequestHistory, TicketCategoryReportingTag
from analyst_tickets.models import TimeSheetEntry
from account.models import Subscription, User

USERNAME = 'test'
EMAIL = 'mail@example.com'
PASSWORD = 'password'
LOGIN_URL = reverse_lazy('auth_login')
PERMISSION_URL = reverse_lazy('permissions-error')
NEXT = '?next='
NOW = timezone.now()
YEAR = timedelta(days=365)


class TestAnalystFileSearchView(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestAnalystFileSearchView, cls).setUpClass()
        mommy.make(Group, name="Analyst")
        cls.content_type = mommy.make('ContentType', app_label='global_permission')
        cls.content_type.model = 'global_permission'
        cls.content_type.save()
        cls.user = User.objects.create_user(EMAIL, PASSWORD)
        cls.perm = mommy.make('Permission', codename='view_user_data', content_type=cls.content_type)

    def setUp(self):
        self.user.user_permissions.add(self.perm)
        self.user.save()
        self.client.login(username=EMAIL, password=PASSWORD)
        self.url = reverse('analyst_file_search')

    def test_analyst_file_search_view_not_logged_in(self):
        self.client.logout()
        result = self.client.get(self.url)
        self.assertRedirects(result, LOGIN_URL + NEXT + self.url)

    def test_analyst_file_search_view_permission_error(self):
        self.user.user_permissions.remove(self.perm)
        self.user.save()
        result = self.client.get(self.url)
        self.assertRedirects(result, PERMISSION_URL + NEXT + self.url)

    def test_analyst_file_search_view_request_not_ajax(self):
        result = self.client.get(self.url)
        self.assertEqual(result.status_code, 200)
        self.assertTemplateUsed(result, 'analyst/file-search.html')

    def test_analyst_file_search_view_get(self):
        ajax_header = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
        result = self.client.get(self.url, data={'filename': 'file'}, **ajax_header)
        self.assertEqual(result.status_code, 200)
        self.assertTemplateUsed(result, 'analyst/file-search.html')

    def test_analyst_file_search_view_post(self):
        for x in range(3):
            mommy.make(EngineDataFile, name='file{}'.format(x), processed=True)
        mommy.make(EngineDataFile, name='abc', processed=True)
        ajax_header = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
        result = self.client.post(self.url, data={'filename': 'file'}, **ajax_header)
        self.assertEqual(result.status_code, 200)
        self.assertTemplateUsed(result, 'analyst/_file-list.html')
        self.assertEqual(result.context['edfs'].count(), 3)


class TestDownloadEdfView(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestDownloadEdfView, cls).setUpClass()
        mommy.make(Group, name="Analyst")
        cls.content_type = mommy.make('ContentType', app_label='global_permission')
        cls.content_type.model = 'global_permission'
        cls.content_type.save()
        cls.user = User.objects.create_user(EMAIL, PASSWORD)
        cls.perm = mommy.make('Permission', codename='download_flight_data', content_type=cls.content_type)

    def setUp(self):
        self.user.user_permissions.add(self.perm)
        self.user.save()
        self.client.login(username=EMAIL, password=PASSWORD)
        self.edf = mommy.make(EngineDataFile)
        self.url = reverse('download_edf', args=[self.edf.id])

    def test_download_edf_view_not_logged_in(self):
        self.client.logout()
        result = self.client.get(self.url)
        self.assertRedirects(result, LOGIN_URL + NEXT + self.url)

    def test_download_edf_view_no_permission(self):
        self.user.user_permissions.remove(self.perm)
        self.user.save()
        result = self.client.get(self.url)
        self.assertEqual(result.status_code, 200)
        self.assertTemplateUsed(result, 'skeletons/basic.html')
        self.assertEqual(result.context['text'], 'File does not exist or download not allowed.')

    @patch('files.models.EngineDataFile.get_url')
    def test_download_edf_view_no_permission_but_owner(self, mock_get_data):
        example_url = 'http://example.com'
        mock_get_data.return_value = example_url
        self.user.user_permissions.remove(self.perm)
        self.user.save()
        self.edf.user = self.user
        self.edf.save()
        result = self.client.get(self.url)
        self.assertRedirects(result, example_url, fetch_redirect_response=False)

    @patch('files.models.EngineDataFile.get_url')
    def test_download_edf_view(self, mock_get_data):
        example_url = 'http://example.com'
        mock_get_data.return_value = example_url
        result = self.client.get(self.url)
        self.assertRedirects(result, example_url, fetch_redirect_response=False)


class TestDownloadRawDataView(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestDownloadRawDataView, cls).setUpClass()
        mommy.make(Group, name="Analyst")
        cls.content_type = mommy.make('ContentType', app_label='global_permission')
        cls.content_type.model = 'global_permission'
        cls.content_type.save()
        cls.user = User.objects.create_user(EMAIL, PASSWORD)
        cls.perm = mommy.make('Permission', codename='download_flight_data', content_type=cls.content_type)

    def setUp(self):
        self.user.user_permissions.add(self.perm)
        self.user.save()
        self.client.login(username=EMAIL, password=PASSWORD)
        self.flight = mommy.make(Flight)
        self.url = reverse('download_raw_data', args=[self.flight.id])

    def test_download_raw_data_view_not_logged_in(self):
        self.client.logout()
        result = self.client.get(self.url)
        self.assertRedirects(result, LOGIN_URL + NEXT + self.url)

    def test_download_edf_view_no_permission(self):
        self.user.user_permissions.remove(self.perm)
        self.user.save()
        result = self.client.get(self.url)
        self.assertEqual(result.status_code, 200)
        self.assertTemplateUsed(result, 'skeletons/basic.html')
        self.assertEqual(result.context['text'], 'File does not exist or download not allowed.')

    @patch('flights.models.Flight.get_url')
    def test_download_edf_view(self, mock_get_data):
        example_url = 'http://example.com'
        mock_get_data.return_value = example_url
        result = self.client.get(self.url)
        self.assertRedirects(result, example_url, fetch_redirect_response=False)


class TestAnalystAircraftSearch(TestCase):
    def setUp(self):
        mommy.make(Group, name="Analyst")
        self.content_type = mommy.make('ContentType', app_label='global_permission')
        self.content_type.model = 'global_permission'
        self.content_type.save()
        self.user = User.objects.create_user(EMAIL, PASSWORD, first_name='John', last_name='Doe')
        self.perm = mommy.make('Permission', codename='view_user_data', content_type=self.content_type)
        self.user.user_permissions.add(self.perm)
        self.user.save()
        self.client.login(username=EMAIL, password=PASSWORD)

    def test_analyst_aircraft_search_not_logged_in(self):
        self.client.logout()
        result = self.client.get(reverse('analyst_aircraft_search'))
        self.assertRedirects(result, reverse('auth_login') + '?next=' + reverse('analyst_aircraft_search'))

    def test_analyst_aircraft_search_permission_denied(self):
        self.user.user_permissions.remove(self.perm)
        result = self.client.get(reverse('analyst_aircraft_search'))
        self.assertRedirects(result, reverse('permissions-error') + '?next=' + reverse('analyst_aircraft_search'))

    def test_analyst_aircraft_search_get(self):
        data = {
            'search': 'test'
        }
        result = self.client.get(reverse('analyst_aircraft_search'), data=data)
        self.assertTemplateUsed(result, 'analyst/aircraft-search.html')
        self.assertEqual(result.context['search_term'], data['search'])

    @patch('analyst.views.get_all_mx_aircraft_and_owners', return_value=[])
    def test_analyst_aircraft_search_post(self, *args, **kwargs):
        ajax_header = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
        model = mommy.make(AircraftModel, twin=False, name='AMODEL')
        amfr = mommy.make(AircraftManufacturer, name='AMFR')
        emfr = mommy.make(EngineManufacturer, name='EMFR')
        emodel = mommy.make(EngineModel, name='EMODLE')
        emmfr = mommy.make(EngineMonitorManufacturer, name='EMMFR')
        emmodel = mommy.make(EngineMonitorModel, name='EMMODEL')
        aircraft = mommy.make(Aircraft, user=self.user, registration_no='N123', aircraft_model=model,
                              engine_manufacturer=emfr,
                              engine_model=emodel,
                              engine_monitor_manufacturer=emmfr,
                              engine_monitor_model=emmodel,
                              aircraft_manufacturer=amfr,
                              hidden=0)
        data = {
            'search_term': 'emf'
        }
        mommy.make(Subscription, aircraft=aircraft, end_date=timezone.now() + timedelta(days=100))
        result = self.client.post(reverse('analyst_aircraft_search'), data=data, **ajax_header)
        self.assertTemplateUsed(result, 'analyst/_aircraft-list.html')
        self.assertEqual(aircraft, result.context['aircraft'][0])

    @patch('analyst.views.get_all_mx_aircraft_and_owners', return_value=[])
    def test_analyst_aircraft_search_post_without_aircraft_user(self, *args, **kwargs):
        ajax_header = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
        model = mommy.make(AircraftModel, twin=False, name='AMODEL')
        amfr = mommy.make(AircraftManufacturer, name='AMFR')
        emfr = mommy.make(EngineManufacturer, name='EMFR')
        emodel = mommy.make(EngineModel, name='EMODLE')
        emmfr = mommy.make(EngineMonitorManufacturer, name='EMMFR')
        emmodel = mommy.make(EngineMonitorModel, name='EMMODEL')
        aircraft = mommy.make(Aircraft, registration_no='N123', aircraft_model=model,
                              engine_manufacturer=emfr,
                              engine_model=emodel,
                              engine_monitor_manufacturer=emmfr,
                              engine_monitor_model=emmodel,
                              aircraft_manufacturer=amfr,
                              hidden=0)
        data = {
            'search_term': 'emf'
        }
        mommy.make(Subscription, aircraft=aircraft, end_date=timezone.now() + timedelta(days=100))
        result = self.client.post(reverse('analyst_aircraft_search'), data=data, **ajax_header)
        self.assertTemplateUsed(result, 'analyst/_aircraft-list.html')
        self.assertEqual(len(result.context['aircraft']), 0)

    @patch('analyst.views.get_all_mx_aircraft_and_owners', return_value=[])
    def test_analyst_aircraft_search_post_without_data(self, *args, **kwargs):
        ajax_header = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
        model = mommy.make(AircraftModel, twin=False, name='AMODEL')
        amfr = mommy.make(AircraftManufacturer, name='AMFR')
        emfr = mommy.make(EngineManufacturer, name='EMFR')
        emodel = mommy.make(EngineModel, name='EMODLE')
        emmfr = mommy.make(EngineMonitorManufacturer, name='EMMFR')
        emmodel = mommy.make(EngineMonitorModel, name='EMMODEL')
        aircraft = mommy.make(Aircraft, user=self.user, registration_no='N123', aircraft_model=model,
                              engine_manufacturer=emfr,
                              engine_model=emodel,
                              engine_monitor_manufacturer=emmfr,
                              engine_monitor_model=emmodel,
                              aircraft_manufacturer=amfr,
                              hidden=0)
        data = {
        }
        mommy.make(Subscription, aircraft=aircraft, end_date=timezone.now() + timedelta(days=100))
        result = self.client.post(reverse('analyst_aircraft_search'), data=data, **ajax_header)
        self.assertTemplateUsed(result, 'analyst/_aircraft-list.html')
        self.assertEqual(len(result.context['aircraft']), 0)


class TestGenerateReportView(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestGenerateReportView, cls).setUpClass()
        cls.analyst = mommy.make(Group, name="Analyst")
        cls.content_type = mommy.make('ContentType', app_label='global_permission')
        cls.content_type.model = 'global_permission'
        cls.content_type.save()
        cls.user = User.objects.create_user(EMAIL, PASSWORD)
        cls.perm = mommy.make('Permission', codename='manage_sa_reports', content_type=cls.content_type)
        support = mommy.make(Group, name='SA Support')
        analyst_user = mommy.make(User, email='analyst@sa.com')
        support_user = mommy.make(User, email='support@sa.com')
        analyst_user.groups.add(cls.analyst)
        support_user.groups.add(support)

    def setUp(self):
        self.user.user_permissions.add(self.perm)
        self.user.save()
        self.client.login(username=EMAIL, password=PASSWORD)
        aircraft_model = mommy.make(AircraftModel, twin=False)
        aircraft = mommy.make(Aircraft, user=self.user, aircraft_model=aircraft_model)
        self.flight = mommy.make(Flight, aircraft=aircraft)
        self.ticket = mommy.make(TicketRequest, trash=0, user=self.user, aircraft=aircraft)
        self.url = reverse('generate_report', args=[self.ticket.id, self.flight.id])

    def test_generate_report_view_not_logged_in(self):
        self.client.logout()
        result = self.client.get(self.url)
        self.assertRedirects(result, reverse('auth_login') + '?next=' + self.url)

    def test_generate_report_view_permission_denied(self):
        self.user.user_permissions.remove(self.perm)
        result = self.client.get(self.url)
        self.assertRedirects(result, reverse('permissions-error') + '?next=' + self.url)

    def test_generate_report_view_ticket_not_exist(self):
        result = self.client.get(reverse('generate_report', args=[30, self.flight.id]))
        self.assertTemplateUsed(result, 'tickets/ticket_not_public.html')

    def test_generate_report_view_already_exist(self):
        mommy.make(FlightReport, ticket=self.ticket, flight=self.flight)
        result = self.client.get(self.url)
        self.assertTemplateUsed(result, 'skeletons/basic.html')
        self.assertEqual(result.context['text'], "A report already exists for this ticket/flight combination.")

    def test_generate_report_view(self):
        mommy.make(TicketRequestHistory, request=self.ticket, dt_gmt_change=12,
                   note='Test\nLine')
        result = self.client.get(self.url)
        self.assertTemplateUsed(result, 'analyst/report-form.html')
        self.assertEqual(result.context['flight_forms'][0].initial['ticket'], self.ticket)
        self.assertEqual(result.context['paste_report'], None)

    def test_generate_report_view_ticket_clipboard(self):
        report = mommy.make(FlightReport, flight=self.flight)
        entry = mommy.make(FlightReportClipboadEntry, user=self.user, report=report)
        mommy.make(TicketRequestHistory, request=self.ticket, dt_gmt_change=12,
                   note='Test\nLine')
        result = self.client.get(self.url)
        self.assertTemplateUsed(result, 'analyst/report-form.html')
        self.assertEqual(result.context['flight_forms'][0].initial['ticket'], self.ticket)
        self.assertEqual(result.context['paste_report'],
                         reverse('paste_report', args=[entry.id, self.ticket.id, self.flight.id]))
        self.assertIn("Copying from ticket", result.context['paste_report_data'])

    def test_generate_report_view_ticket_clipboard_different_twins(self):
        aircraft_model = mommy.make(AircraftModel, twin=True)
        aircraft = mommy.make(Aircraft, user=self.user, aircraft_model=aircraft_model)
        flight = mommy.make(Flight, aircraft=aircraft)
        report = mommy.make(FlightReport, flight=flight)
        entry = mommy.make(FlightReportClipboadEntry, user=self.user, report=report)
        mommy.make(TicketRequestHistory, request=self.ticket, dt_gmt_change=12,
                   note='Test\nLine')
        result = self.client.get(self.url)
        self.assertTemplateUsed(result, 'analyst/report-form.html')
        self.assertEqual(result.context['flight_forms'][0].initial['ticket'], self.ticket)
        self.assertEqual(result.context['paste_report'], 'error')
        self.assertIn("Cannot paste twin engine report into single", result.context['paste_report_error'])

    def test_generate_report_view_ticket_clipboard_different_twins_else(self):
        self.ticket.user = None
        self.ticket.save()
        self.ticket.aircraft.aircraft_model.twin=True
        self.ticket.aircraft.aircraft_model.save()
        aircraft_model = mommy.make(AircraftModel, twin=False)
        aircraft = mommy.make(Aircraft, user=self.user, aircraft_model=aircraft_model)
        flight = mommy.make(Flight, aircraft=aircraft)
        report = mommy.make(FlightReport, flight=flight)
        entry = mommy.make(FlightReportClipboadEntry, user=self.user, report=report)
        mommy.make(TicketRequestHistory, request=self.ticket, dt_gmt_change=12,
                   note='Test\nLine')
        result = self.client.get(self.url)
        self.assertTemplateUsed(result, 'analyst/report-form.html')
        self.assertEqual(result.context['flight_forms'][0].initial['ticket'], self.ticket)
        self.assertEqual(result.context['paste_report'], 'error')
        self.assertIn("Cannot paste single engine report into twin.", result.context['paste_report_error'])

    def test_generate_report_view_twin(self):
        self.ticket.aircraft.aircraft_model.twin = True
        self.ticket.aircraft.aircraft_model.save()
        aircraft_model = mommy.make(AircraftModel, twin=True)
        aircraft = mommy.make(Aircraft, user=self.user, aircraft_model=aircraft_model)
        flight = mommy.make(Flight, aircraft=aircraft)
        sister = mommy.make(FlightReport, flight=flight, engine=2)
        report = mommy.make(FlightReport, flight=flight, engine=1, sister_report=sister)
        entry = mommy.make(FlightReportClipboadEntry, user=self.user, report=report)
        mommy.make(TicketRequestHistory, request=self.ticket, dt_gmt_change=12,
                   note='Test\nLine')
        result = self.client.get(self.url)
        self.assertTemplateUsed(result, 'analyst/report-form.html')
        self.assertEqual(result.context['flight_forms'][0].prefix, str(report.engine))
        self.assertEqual(result.context['flight_forms'][1].prefix, str(sister.engine))

    def test_generate_report_view_post(self):
        aircraft_model = mommy.make(AircraftModel, twin=False)
        aircraft = mommy.make(Aircraft, user=self.user, aircraft_model=aircraft_model)
        flight = mommy.make(Flight, aircraft=aircraft)
        sister = mommy.make(FlightReport, flight=flight, engine=2)
        report = mommy.make(FlightReport, flight=flight, engine=1, sister_report=sister)
        entry = mommy.make(FlightReportClipboadEntry, user=self.user, report=report)
        mommy.make(TicketRequestHistory, request=self.ticket, dt_gmt_change=12,
                   note='Test\nLine')
        data = {
            '0-gami_summary': 'Satisfactory',
            '0-temperatures_summary': 'Caution',
            '0-electrical_summary': 'Alert',
            '0-engine': '1',
            '0-flight': flight.id,
        }
        result = self.client.post(self.url, data=data)
        self.assertEqual(result.url, reverse('edit_report', args=[report.id+1]))

    def test_generate_report_view_post_twin(self):
        self.ticket.aircraft.aircraft_model.twin = True
        self.ticket.aircraft.aircraft_model.save()
        aircraft_model = mommy.make(AircraftModel, twin=True)
        aircraft = mommy.make(Aircraft, user=self.user, aircraft_model=aircraft_model)
        flight = mommy.make(Flight, aircraft=aircraft)
        sister = mommy.make(FlightReport, flight=flight, engine=2)
        report = mommy.make(FlightReport, flight=flight, engine=1, sister_report=sister)
        entry = mommy.make(FlightReportClipboadEntry, user=self.user, report=report)
        mommy.make(TicketRequestHistory, request=self.ticket, dt_gmt_change=12,
                   note='Test\nLine')
        data = {
            '1-gami_summary': 'Satisfactory',
            '1-temperatures_summary': 'Caution',
            '1-electrical_summary': 'Alert',
            '1-engine': '1',
            '1-flight': flight.id,
            '2-gami_summary': 'Satisfactory',
            '2-temperatures_summary': 'Caution',
            '2-electrical_summary': 'Alert',
            '2-engine': '1',
            '2-flight': flight.id,
        }
        result = self.client.post(self.url, data=data)
        self.assertEqual(result.url, reverse('edit_report', args=[report.id + 1]))


class TestCopyReport(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestCopyReport, cls).setUpClass()
        cls.analyst = mommy.make(Group, name="Analyst")
        cls.content_type = mommy.make('ContentType', app_label='global_permission')
        cls.content_type.model = 'global_permission'
        cls.content_type.save()
        cls.user = User.objects.create_user(EMAIL, PASSWORD)
        cls.perm = mommy.make('Permission', codename='manage_sa_reports', content_type=cls.content_type)

    def setUp(self):
        self.user.user_permissions.add(self.perm)
        self.user.save()
        self.client.login(username=EMAIL, password=PASSWORD)
        self.report = mommy.make(FlightReport)
        self.url = reverse('copy_report', args=[self.report.id])

    def test_copy_report_not_logged_in(self):
        self.client.logout()
        result = self.client.get(self.url)
        self.assertRedirects(result, reverse('auth_login') + '?next=' + self.url)

    def test_copy_report_permission_denied(self):
        self.user.user_permissions.remove(self.perm)
        result = self.client.get(self.url)
        self.assertRedirects(result, reverse('permissions-error') + '?next=' + self.url)

    def test_copy_report(self):
        entry = mommy.make(FlightReportClipboadEntry, user=self.user)
        result = self.client.get(self.url)
        existing_report = FlightReportClipboadEntry.objects.filter(id=entry.id)
        new_report = FlightReportClipboadEntry.objects.filter(report=self.report)
        self.assertEqual(len(existing_report), 0)
        self.assertEqual(len(new_report), 1)
        self.assertIn(b'status', result.content)
        self.assertIn(b'ok', result.content)


class TestPasteReport(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestPasteReport, cls).setUpClass()
        cls.analyst = mommy.make(Group, name="Analyst")
        cls.content_type = mommy.make('ContentType', app_label='global_permission')
        cls.content_type.model = 'global_permission'
        cls.content_type.save()
        cls.user = User.objects.create_user(EMAIL, PASSWORD)
        cls.perm = mommy.make('Permission', codename='manage_sa_reports', content_type=cls.content_type)

    def setUp(self):
        self.user.user_permissions.add(self.perm)
        self.user.save()
        self.client.login(username=EMAIL, password=PASSWORD)
        self.flight = mommy.make(Flight)
        self.ticket = mommy.make(TicketRequest, user=self.user)
        self.report = mommy.make(FlightReport, flight=self.flight, ticket=self.ticket)
        self.url = reverse('paste_report', args=[self.report.id, self.ticket.id, self.flight.id])

    def test_paste_report_not_logged_in(self):
        self.client.logout()
        result = self.client.get(self.url)
        self.assertRedirects(result, reverse('auth_login') + '?next=' + self.url)

    def test_paste_report_permission_denied(self):
        self.user.user_permissions.remove(self.perm)
        result = self.client.get(self.url)
        self.assertRedirects(result, reverse('permissions-error') + '?next=' + self.url)

    def test_paste_report_get(self):
        result = self.client.get(self.url)
        self.assertEqual(b'Not supported', result.content)

    def test_paste_report_post(self):
        mommy.make(TicketRequestHistory, request=self.ticket, dt_gmt_change=12,
                   note='Test\nLine')
        support = mommy.make(Group, name='SA Support')
        analyst_user = mommy.make(User, email='analyst@sa.com')
        support_user = mommy.make(User, email='support@sa.com')
        analyst_user.groups.add(self.analyst)
        support_user.groups.add(support)
        aircraft_model = mommy.make(AircraftModel, twin=False)
        aircraft = mommy.make(Aircraft, user=self.user, aircraft_model=aircraft_model)
        self.report.flight.aircraft = aircraft
        self.report.flight.save()
        result = self.client.post(self.url)
        existing_report = FlightReport.objects.filter(flight=self.flight, ticket=self.ticket).last()
        self.assertEqual(existing_report.client_comments, 'Test<br/>Line')
        self.assertEqual(result.url, reverse('edit_report', args=[existing_report.id]))

    def test_paste_report_post_twin(self):
        mommy.make(TicketRequestHistory, request=self.ticket, dt_gmt_change=12,
                   note='Test\nLine')
        support = mommy.make(Group, name='SA Support')
        analyst_user = mommy.make(User, email='analyst@sa.com')
        support_user = mommy.make(User, email='support@sa.com')
        analyst_user.groups.add(self.analyst)
        support_user.groups.add(support)
        aircraft_model = mommy.make(AircraftModel, twin=True)
        aircraft = mommy.make(Aircraft, user=self.user, aircraft_model=aircraft_model)
        report = mommy.make(FlightReport, flight=self.flight, ticket=self.ticket, engine=2)
        self.report.engine = 1
        self.report.sister_report = report
        self.report.save()
        self.report.flight.aircraft = aircraft
        self.report.flight.save()
        result = self.client.post(self.url)
        existing_report = FlightReport.objects.filter(flight=self.flight, ticket=self.ticket)[2]
        self.assertEqual(existing_report.client_comments, 'Test<br/>Line')
        self.assertEqual(result.url, reverse('edit_report', args=[existing_report.id]))


class TestPreviewReportMx(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestPreviewReportMx, cls).setUpClass()
        cls.analyst = mommy.make(Group, name="Analyst")
        cls.content_type = mommy.make('ContentType', app_label='global_permission')
        cls.content_type.model = 'global_permission'
        cls.content_type.save()
        cls.user = User.objects.create_user(EMAIL, PASSWORD)
        cls.perm = mommy.make('Permission', codename='view_mx_reports', content_type=cls.content_type)

    def setUp(self):
        self.user.user_permissions.add(self.perm)
        self.user.save()
        self.client.login(username=EMAIL, password=PASSWORD)
        self.flight = mommy.make(Flight)
        self.url = reverse('preview_report_mx', args=[self.flight.id])

    def test_preview_report_mx_not_logged_in(self):
        self.client.logout()
        result = self.client.get(self.url)
        self.assertRedirects(result, reverse('auth_login') + '?next=' + self.url)

    def test_preview_report_mx_permission_denied(self):
        self.user.user_permissions.remove(self.perm)
        result = self.client.get(self.url)
        self.assertRedirects(result, reverse('permissions-error') + '?next=' + self.url)

    def test_preview_report_mx(self):
        result = self.client.get(self.url)
        self.assertTemplateUsed(result, 'tickets/preview-report.html')
        self.assertEqual(reverse('download_report_mx', args=[self.flight.id, 0]), result.context['pdf_preview'])


class TestDownloadReportMx(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestDownloadReportMx, cls).setUpClass()
        cls.analyst = mommy.make(Group, name="Analyst")
        cls.content_type = mommy.make('ContentType', app_label='global_permission')
        cls.content_type.model = 'global_permission'
        cls.content_type.save()
        cls.user = User.objects.create_user(EMAIL, PASSWORD)
        cls.perm = mommy.make('Permission', codename='view_mx_reports', content_type=cls.content_type)

    def setUp(self):
        self.user.user_permissions.add(self.perm)
        self.user.save()
        self.client.login(username=EMAIL, password=PASSWORD)
        self.flight = mommy.make(Flight)
        self.url = reverse('download_report_mx', args=[self.flight.id, 1])

    def test_download_report_mx_not_logged_in(self):
        self.client.logout()
        result = self.client.get(self.url)
        self.assertRedirects(result, reverse('auth_login') + '?next=' + self.url)

    def test_download_report_mx_permission_denied(self):
        self.user.user_permissions.remove(self.perm)
        result = self.client.get(self.url)
        self.assertRedirects(result, reverse('permissions-error') + '?next=' + self.url)

    @patch('analyst.reports.PdfReport.generate', return_value=HttpResponse(content_type='application/pdf'))
    def test_download_report_mx(self, *args, **kwargs):
        result = self.client.get(self.url)
        self.assertEqual(result._headers['content-type'], ('Content-Type', 'application/pdf'))


class TestPreviewReport(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestPreviewReport, cls).setUpClass()
        cls.analyst = mommy.make(Group, name="Analyst")
        cls.content_type = mommy.make('ContentType', app_label='global_permission')
        cls.content_type.model = 'global_permission'
        cls.content_type.save()
        cls.user = User.objects.create_user(EMAIL, PASSWORD)
        cls.perm = mommy.make('Permission', codename='view_sa_reports', content_type=cls.content_type)

    def setUp(self):
        self.user.user_permissions.add(self.perm)
        self.user.save()
        self.client.login(username=EMAIL, password=PASSWORD)
        self.flight = mommy.make(Flight)
        self.report = mommy.make(FlightReport, flight=self.flight)
        self.url = reverse('preview_report', args=[self.flight.id, self.report.id])

    def test_preview_report_not_logged_in(self):
        self.client.logout()
        result = self.client.get(self.url)
        self.assertRedirects(result, reverse('auth_login') + '?next=' + self.url)

    def test_preview_report_permission_denied(self):
        self.user.user_permissions.remove(self.perm)
        result = self.client.get(self.url)
        self.assertRedirects(result, reverse('permissions-error') + '?next=' + self.url)

    def test_preview_report(self):
        result = self.client.get(self.url)
        self.assertTemplateUsed(result, 'tickets/preview-report.html')
        self.assertEqual(reverse('download_report', args=[self.report.id, self.flight.id, 0]),
                         result.context['pdf_preview'])


class TestDownloadReportView(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestDownloadReportView, cls).setUpClass()
        cls.analyst = mommy.make(Group, name="Analyst")
        cls.content_type = mommy.make('ContentType', app_label='global_permission')
        cls.content_type.model = 'global_permission'
        cls.content_type.save()
        cls.user = User.objects.create_user(EMAIL, PASSWORD)
        cls.perm = mommy.make('Permission', codename='view_sa_reports', content_type=cls.content_type)

    def setUp(self):
        self.user.user_permissions.add(self.perm)
        self.user.save()
        self.client.login(username=EMAIL, password=PASSWORD)
        self.flight = mommy.make(Flight)
        self.report = mommy.make(FlightReport, flight=self.flight)
        self.url = reverse('download_report', args=[self.report.id, self.flight.id, 1])

    def test_download_report_view_not_logged_in(self):
        self.client.logout()
        result = self.client.get(self.url)
        self.assertRedirects(result, reverse('auth_login') + '?next=' + self.url)

    def test_download_report_view_permission_denied(self):
        self.user.user_permissions.remove(self.perm)
        result = self.client.get(self.url)
        self.assertRedirects(result, reverse('permissions-error') + '?next=' + self.url)

    def test_download_report_view(self):
        result = self.client.get(self.url)
        self.assertTemplateUsed(result, 'tickets/ticket_not_public.html')

    @patch('analyst.reports.PdfReport.generate', return_value=HttpResponse(content_type='application/pdf'))
    def test_download_report_view_with_ticket(self, *args, **kwargs):
        ticket = mommy.make(TicketRequest, user=self.user)
        self.report.ticket = ticket
        self.report.save()
        mommy.make(TicketRequestHistory, request=ticket, dt_gmt_change=12,
                   note='Test\nLine')
        support = mommy.make(Group, name='SA Support')
        analyst_user = mommy.make(User, email='analyst@sa.com')
        support_user = mommy.make(User, email='support@sa.com')
        analyst_user.groups.add(self.analyst)
        support_user.groups.add(support)
        result = self.client.get(self.url)
        self.assertEqual(result._headers['content-type'], ('Content-Type', 'application/pdf'))


class TestDeleteReportView(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestDeleteReportView, cls).setUpClass()
        cls.analyst = mommy.make(Group, name="Analyst")
        cls.content_type = mommy.make('ContentType', app_label='global_permission')
        cls.content_type.model = 'global_permission'
        cls.content_type.save()
        cls.user = User.objects.create_user(EMAIL, PASSWORD)
        cls.perm = mommy.make('Permission', codename='manage_sa_reports', content_type=cls.content_type)

    def setUp(self):
        self.user.user_permissions.add(self.perm)
        self.user.save()
        self.client.login(username=EMAIL, password=PASSWORD)
        self.report = mommy.make(FlightReport)
        self.url = reverse('delete_report', args=[self.report.id])

    def test_delete_report_view_not_logged_in(self):
        self.client.logout()
        result = self.client.get(self.url)
        self.assertRedirects(result, reverse('auth_login') + '?next=' + self.url)

    def test_delete_report_view_permission_denied(self):
        self.user.user_permissions.remove(self.perm)
        result = self.client.get(self.url)
        self.assertRedirects(result, reverse('permissions-error') + '?next=' + self.url)

    def test_delete_report_view_get(self):
        result = self.client.get(self.url)
        self.assertEqual(b'Not Supported', result.content)

    def test_delete_report_view_post(self):
        sister = mommy.make(FlightReport)
        self.report.sister_report = sister
        self.report.save()
        result = self.client.post(self.url)
        report = FlightReport.objects.filter(id=self.report.id)
        self.assertEqual(len(report), 0)
        self.assertEqual(result.url, reverse('analyst_dashboard'))


class TestMxReportsView(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestMxReportsView, cls).setUpClass()
        cls.analyst = mommy.make(Group, name="Analyst")
        cls.content_type = mommy.make('ContentType', app_label='global_permission')
        cls.content_type.model = 'global_permission'
        cls.content_type.save()
        cls.user = User.objects.create_user(EMAIL, PASSWORD)
        cls.perm = mommy.make('Permission', codename='view_mx_reports', content_type=cls.content_type)

    def setUp(self):
        self.user.user_permissions.add(self.perm)
        self.user.save()
        self.client.login(username=EMAIL, password=PASSWORD)
        self.flight = mommy.make(Flight)
        self.report = mommy.make(FlightReport, flight=self.flight)
        self.url = reverse('mx_reports')

    def test_mx_reports_view_not_logged_in(self):
        self.client.logout()
        result = self.client.get(self.url)
        self.assertEqual(result.url, reverse('permissions-error') + '?next=' + self.url)

    def test_mx_reports_view_permission_denied(self):
        self.user.user_permissions.remove(self.perm)
        result = self.client.get(self.url)
        self.assertEqual(result.url, reverse('permissions-error') + '?next=' + self.url)

    def test_mx_reports_view(self):
        result = self.client.get(self.url)
        self.assertTemplateUsed(result, 'tickets/mx-reports.html')
        self.assertEqual(len(result.context['flights']), 1)


class TestSendReportToUserView(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestSendReportToUserView, cls).setUpClass()
        cls.analyst = mommy.make(Group, name="Analyst")
        cls.content_type = mommy.make('ContentType', app_label='global_permission')
        cls.content_type.model = 'global_permission'
        cls.content_type.save()
        cls.user = User.objects.create_user(EMAIL, PASSWORD, first_name='John', last_name='Doe')
        cls.perm = mommy.make('Permission', codename='manage_own_timesheets', content_type=cls.content_type)
        cls.perm2 = mommy.make('Permission', codename='update_all_tickets', content_type=cls.content_type)

    def setUp(self):
        self.user.user_permissions.add(self.perm)
        self.user.user_permissions.add(self.perm2)
        self.user.save()
        self.client.login(username=EMAIL, password=PASSWORD)
        self.aircraft = mommy.make(Aircraft, user=self.user)
        self.flight = mommy.make(Flight, aircraft=self.aircraft, date=timezone.now())
        self.ticket = mommy.make(TicketRequest, user=self.user, trash=0)
        self.report = mommy.make(FlightReport, flight=self.flight, ticket=self.ticket)
        self.url = reverse('send_report', args=[self.user.id, self.ticket.id, self.report.id])

    def test_send_report_to_user_view_not_logged_in(self):
        self.client.logout()
        result = self.client.get(self.url)
        self.assertEqual(result.url, reverse('auth_login') + '?next=' + self.url)

    def test_send_report_to_user_view_permission_denied(self):
        self.user.user_permissions.remove(self.perm)
        self.user.user_permissions.remove(self.perm2)
        result = self.client.get(self.url)
        self.assertEqual(result.url, reverse('permissions-error') + '?next=' + self.url)

    def test_send_report_to_user_view_get_engine(self):
        self.report.engine = 0
        self.report.save()
        result = self.client.get(self.url)
        self.assertEqual(result.context['form'].initial['analyst_comments'],
                         u"Hi {},\n\nI have attached the SavvyAnalysis report for your {:%b %d, %Y} flight.\n\n{} {}".
                         format(self.ticket.user.first_name,
                                self.flight.date,
                                self.user.first_name,
                                self.user.last_name,
                                ))
        self.assertTemplateUsed(result, 'analyst/send-report.html')
        self.assertEqual(int(result.context['ticket_id']), self.ticket.id)

    def test_send_report_to_user_view_get_with_user(self):
        self.aircraft.owner_email = 'test@aircraft.com'
        self.aircraft.save()
        result = self.client.get(reverse('send_report', args=[0, self.ticket.id, self.report.id]))
        self.assertEqual(result.context['owner_email'], self.aircraft.owner_email)

    def test_send_report_to_user_view_post_invalid(self):
        self.report.engine = 0
        self.report.save()
        post_data = {
            'include_report': True,
        }
        result = self.client.post(self.url, data=post_data)
        self.assertFalse(result.context['form'].is_valid())
        self.assertIn('This field is required', str(result.context['form'].errors['analyst_comments']))

    def test_send_report_to_user_view_post_valid(self):
        self.report.engine = 0
        self.report.save()
        mommy.make(TicketCategoryReportingTag, name="Report Complete")
        mommy.make(TimeSheetEntry, seconds=None, ticket=self.ticket, user=self.user)
        mommy.make(TicketRequestHistory, request=self.ticket, dt_gmt_change=12,
                   note='Test\nLine')
        support = mommy.make(Group, name='SA Support')
        analyst_user = mommy.make(User, email='analyst@sa.com')
        support_user = mommy.make(User, email='support@sa.com')
        analyst_user.groups.add(self.analyst)
        support_user.groups.add(support)
        post_data = {
            'include_report': True,
            'analyst_comments': 'Test comments',
            'minutes': '5',
            'close_ticket': True,
            'include_profiles': True,
            'include_howto_download': True
        }
        result = self.client.post(self.url, data=post_data)
        self.assertEqual(result.url, reverse('analyst_ticket', args=[self.ticket.id]))

    def test_send_report_to_user_view_post_valid_without_ticket(self):
        self.ticket.user = None
        self.ticket.save()
        self.report.engine = 0
        self.report.save()
        post_data = {
            'include_report': True,
            'analyst_comments': 'Test comments',
            'minutes': '5',
            'close_ticket': True,
            'include_profiles': True,
            'include_howto_download': True
        }
        result = self.client.post(self.url, data=post_data)
        self.assertTemplateUsed(result, 'tickets/ticket_not_public.html')

    def test_send_report_to_user_view_post_valid_minutes_value_error(self):
        self.report.engine = 0
        self.report.save()
        mommy.make(TicketCategoryReportingTag, name="Report Complete")
        mommy.make(TimeSheetEntry, seconds=None, ticket=self.ticket, user=self.user)
        mommy.make(TicketRequestHistory, request=self.ticket, dt_gmt_change=12,
                   note='Test\nLine')
        support = mommy.make(Group, name='SA Support')
        analyst_user = mommy.make(User, email='analyst@sa.com')
        support_user = mommy.make(User, email='support@sa.com')
        analyst_user.groups.add(self.analyst)
        support_user.groups.add(support)
        post_data = {
            'include_report': True,
            'analyst_comments': 'Test comments',
            'minutes': '',
            'close_ticket': True,
            'include_profiles': True,
            'include_howto_download': True
        }
        result = self.client.post(self.url, data=post_data)
        self.assertEqual(result.url, reverse('analyst_ticket', args=[self.ticket.id]))


class TestClientNotesView(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestClientNotesView, cls).setUpClass()
        cls.analyst = mommy.make(Group, name="Analyst")
        cls.content_type = mommy.make('ContentType', app_label='global_permission')
        cls.content_type.model = 'global_permission'
        cls.content_type.save()
        cls.user = User.objects.create_user(EMAIL, PASSWORD, first_name='John', last_name='Doe')
        cls.perm = mommy.make('Permission', codename='edit_client_notes', content_type=cls.content_type)

    def setUp(self):
        self.user.user_permissions.add(self.perm)
        self.user.save()
        self.client.login(username=EMAIL, password=PASSWORD)
        self.url = reverse('analyst_client_notes', args=[self.user.id])

    def test_client_notes_view_not_logged_in(self):
        self.client.logout()
        result = self.client.get(self.url)
        self.assertEqual(result.url, reverse('auth_login') + '?next=' + self.url)

    def test_client_notes_view_permission_denied(self):
        self.user.user_permissions.remove(self.perm)
        result = self.client.get(self.url)
        self.assertEqual(result.url, reverse('permissions-error') + '?next=' + self.url)

    def test_client_notes_view_get(self):
        self.user.analyst_notes = 'Test'
        self.user.save()
        result = self.client.get(self.url)
        self.assertTemplateUsed(result, 'analyst/client_notes.html')
        self.assertEqual(result.context['form'].initial['notes'], 'Test')

    def test_client_notes_view_post(self):
        post_data = {
            'notes': 'Dummy Notes'
        }

        result = self.client.post(self.url, data=post_data)
        user = User.objects.get(id=self.user.id)
        self.assertEqual(user.analyst_notes, post_data['notes'])
        self.assertEqual(result.url, reverse('analyst_client_notes', args=[self.user.id]))

    def test_client_notes_view_invalid_method(self):
        result = self.client.delete(self.url)
        self.assertEqual(b'Unsupported method', result.content)


class TestFlightReportSearchView(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestFlightReportSearchView, cls).setUpClass()
        cls.analyst = mommy.make(Group, name="Analyst")
        cls.content_type = mommy.make('ContentType', app_label='global_permission')
        cls.content_type.model = 'global_permission'
        cls.content_type.save()
        cls.user = User.objects.create_user(EMAIL, PASSWORD, first_name='John', last_name='Doe')
        cls.perm = mommy.make('Permission', codename='search_flight_reports', content_type=cls.content_type)

    def setUp(self):
        self.user.user_permissions.add(self.perm)
        self.user.save()
        self.client.login(username=EMAIL, password=PASSWORD)
        self.url = reverse('analyst_flight_report_search')

    def test_flight_report_search_view_not_logged_in(self):
        self.client.logout()
        result = self.client.get(self.url)
        self.assertEqual(result.url, reverse('auth_login') + '?next=' + self.url)

    def test_flight_report_search_view_permission_denied(self):
        self.user.user_permissions.remove(self.perm)
        result = self.client.get(self.url)
        self.assertEqual(result.status_code, 403)

    def test_flight_report_search_view_get(self):
        result = self.client.get(self.url)
        self.assertTemplateUsed(result, 'analyst/flight-report-search.html')

    def test_flight_report_search_view_post(self):
        aircraft = mommy.make(Aircraft, registration_no='N123', user=self.user)
        flight = mommy.make(Flight, aircraft=aircraft)
        ticket = mommy.make(TicketRequest, aircraft=aircraft, user=self.user)
        report = mommy.make(FlightReport, flight=flight, ticket=ticket)
        post_data = {
            'ticket_id': ticket.id,
            'aircraft_registration': 'N123',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': EMAIL,
        }
        result = self.client.post(self.url, data=post_data)
        self.assertTemplateUsed(result, 'analyst/flight-reports.html')
        self.assertEqual(len(result.context['flight_reports']), 1)

    def test_flight_report_search_view_post_invalid_ticket_id(self):
        aircraft = mommy.make(Aircraft, registration_no='N123', user=self.user)
        flight = mommy.make(Flight, aircraft=aircraft)
        ticket = mommy.make(TicketRequest, aircraft=aircraft, user=self.user)
        report = mommy.make(FlightReport, flight=flight, ticket=ticket)
        post_data = {
            'ticket_id': 'm',
            'aircraft_registration': 'N123',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': EMAIL,
        }
        result = self.client.post(self.url, data=post_data)
        self.assertTemplateUsed(result, 'analyst/flight-reports.html')
        self.assertEqual(len(result.context['flight_reports']), 1)


class TestGenerateMxReportView(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestGenerateMxReportView, cls).setUpClass()
        cls.analyst = mommy.make(Group, name="Analyst")
        cls.content_type = mommy.make('ContentType', app_label='global_permission')
        cls.content_type.model = 'global_permission'
        cls.content_type.save()
        cls.user = User.objects.create_user(EMAIL, PASSWORD, first_name='John', last_name='Doe')
        cls.perm = mommy.make('Permission', codename='view_mx_reports', content_type=cls.content_type)

    def setUp(self):
        self.user.user_permissions.add(self.perm)
        self.user.save()
        self.client.login(username=EMAIL, password=PASSWORD)
        aircraft = mommy.make(Aircraft, user=self.user)
        self.flight = mommy.make(Flight, aircraft=aircraft)
        self.url = reverse('generate_mx_report', args=[self.flight.id])

    def test_generate_mx_report_view_not_logged_in(self):
        self.client.logout()
        result = self.client.get(self.url)
        self.assertEqual(result.url, reverse('auth_login') + '?next=' + self.url)

    def test_generate_mx_report_view_permission_denied(self):
        self.user.user_permissions.remove(self.perm)
        result = self.client.get(self.url)
        self.assertEqual(result.url, reverse('permissions-error') + '?next=' + self.url)

    def test_generate_mx_reports_view_flight_report(self):
        ticket = mommy.make(TicketRequest)
        mommy.make(FlightReport, flight=self.flight, ticket=ticket)
        result = self.client.get(self.url)
        self.assertTemplateUsed(result, 'skeletons/basic.html')
        self.assertEqual("You are trying to create an Mx report where a SavvyAnalysis report already exists.",
                         result.context['text'])

    def test_generate_mx_reports_view_flight_report_without_ticket(self):
        mommy.make(FlightReport, flight=self.flight, ticket=None)
        result = self.client.get(self.url)
        self.assertTemplateUsed(result, 'analyst/report-form.html')
        self.assertEqual(len(result.context['flight_forms']), 1)
        self.assertEqual(result.context['pdf_download'], reverse('download_report_mx', args=[self.flight.id, 1]))
        self.assertEqual(result.context['pdf_preview'], reverse('preview_report_mx', args=[self.flight.id]))

    def test_generate_mx_reports_view_without_flight_reports(self):
        result = self.client.get(self.url)
        self.assertTemplateUsed(result, 'skeletons/basic.html')
        self.assertEqual('Please set aircraft make and model and try again. https://www.savvyanalysis.com%s' % reverse(
            'aircraft_edit', args=[self.flight.aircraft.id]),
                         result.context['text'])

    def test_generate_mx_report_view_aircraft_model(self):
        model = mommy.make(AircraftModel, twin=False)
        self.flight.aircraft.aircraft_model = model
        self.flight.aircraft.save()
        result = self.client.get(self.url)
        self.assertTemplateUsed(result, 'analyst/report-form.html')
        self.assertEqual(len(result.context['flight_forms']), 1)

    def test_generate_mx_report_view_aircraft_model_twin(self):
        model = mommy.make(AircraftModel, twin=True)
        self.flight.aircraft.aircraft_model = model
        self.flight.aircraft.save()
        result = self.client.get(self.url)
        self.assertTemplateUsed(result, 'analyst/report-form.html')
        self.assertEqual(len(result.context['flight_forms']), 2)

    def test_generate_mx_report_view_post_without_permission(self):
        result = self.client.post(self.url)
        self.assertEqual(result.url, reverse('permissions-error'))

    def test_generate_mx_report_view_post(self):
        perm = mommy.make('Permission', codename='manage_mx_reports', content_type=self.content_type)
        self.user.user_permissions.add(perm)
        self.user.save()
        model = mommy.make(AircraftModel, twin=False)
        self.flight.aircraft.aircraft_model = model
        self.flight.aircraft.save()
        data = {
            '0-gami_summary': 'Satisfactory',
            '0-temperatures_summary': 'Caution',
            '0-electrical_summary': 'Alert',
            '0-engine': 0,
            '0-flight': self.flight.id,
        }
        result = self.client.post(self.url, data=data)
        self.assertTemplateUsed(result, 'analyst/report-form.html')
        self.assertEqual(result.context['pdf_download'], reverse('download_report_mx', args=[self.flight.id, 1]))
        self.assertEqual(result.context['pdf_preview'], reverse('preview_report_mx', args=[self.flight.id]))

    def test_generate_mx_report_view_post_with_instance(self):
        mommy.make(FlightReport, ticket=None, flight=self.flight)
        perm = mommy.make('Permission', codename='manage_mx_reports', content_type=self.content_type)
        self.user.user_permissions.add(perm)
        self.user.save()
        model = mommy.make(AircraftModel, twin=False)
        self.flight.aircraft.aircraft_model = model
        self.flight.aircraft.save()
        data = {
            '0-gami_summary': 'Satisfactory',
            '0-temperatures_summary': 'Caution',
            '0-electrical_summary': 'Alert',
            '0-engine': 0,
            '0-flight': self.flight.id,
        }
        result = self.client.post(self.url, data=data)
        self.assertTemplateUsed(result, 'analyst/report-form.html')
        self.assertEqual(result.context['pdf_download'], reverse('download_report_mx', args=[self.flight.id, 1]))
        self.assertEqual(result.context['pdf_preview'], reverse('preview_report_mx', args=[self.flight.id]))

    def test_generate_mx_report_view_post_twin_with_instance(self):
        mommy.make(FlightReport, ticket=None, flight=self.flight, engine=1)
        mommy.make(FlightReport, ticket=None, flight=self.flight, engine=2)
        perm = mommy.make('Permission', codename='manage_mx_reports', content_type=self.content_type)
        self.user.user_permissions.add(perm)
        self.user.save()
        model = mommy.make(AircraftModel, twin=True)
        self.flight.aircraft.aircraft_model = model
        self.flight.aircraft.save()
        data = {
            '1-gami_summary': 'Satisfactory',
            '1-temperatures_summary': 'Caution',
            '1-electrical_summary': 'Alert',
            '1-engine': 0,
            '1-flight': self.flight.id,
            '2-gami_summary': 'Satisfactory',
            '2-temperatures_summary': 'Caution',
            '2-electrical_summary': 'Alert',
            '2-engine': 0,
            '2-flight': self.flight.id,
        }
        result = self.client.post(self.url, data=data)
        self.assertTemplateUsed(result, 'analyst/report-form.html')
        self.assertEqual(result.context['pdf_download'], reverse('download_report_mx', args=[self.flight.id, 1]))
        self.assertEqual(result.context['pdf_preview'], reverse('preview_report_mx', args=[self.flight.id]))

    def test_generate_mx_report_view_post_twin(self):
        perm = mommy.make('Permission', codename='manage_mx_reports', content_type=self.content_type)
        self.user.user_permissions.add(perm)
        self.user.save()
        model = mommy.make(AircraftModel, twin=True)
        self.flight.aircraft.aircraft_model = model
        self.flight.aircraft.save()
        data = {
            '1-gami_summary': 'Satisfactory',
            '1-temperatures_summary': 'Caution',
            '1-electrical_summary': 'Alert',
            '1-engine': 0,
            '1-flight': self.flight.id,
            '2-gami_summary': 'Satisfactory',
            '2-temperatures_summary': 'Caution',
            '2-electrical_summary': 'Alert',
            '2-engine': 0,
            '2-flight': self.flight.id,
        }
        result = self.client.post(self.url, data=data)
        self.assertTemplateUsed(result, 'analyst/report-form.html')
        self.assertEqual(result.context['pdf_download'], reverse('download_report_mx', args=[self.flight.id, 1]))
        self.assertEqual(result.context['pdf_preview'], reverse('preview_report_mx', args=[self.flight.id]))


class TestEditReportView(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestEditReportView, cls).setUpClass()
        cls.analyst = mommy.make(Group, name="Analyst")
        cls.content_type = mommy.make('ContentType', app_label='global_permission')
        cls.content_type.model = 'global_permission'
        cls.content_type.save()
        cls.user = User.objects.create_user(EMAIL, PASSWORD, first_name='John', last_name='Doe')
        cls.perm = mommy.make('Permission', codename='view_sa_reports', content_type=cls.content_type)

    def setUp(self):
        self.user.user_permissions.add(self.perm)
        self.user.save()
        self.client.login(username=EMAIL, password=PASSWORD)
        aircraft = mommy.make(Aircraft, user=self.user)
        self.ticket = mommy.make(TicketRequest, user=self.user, aircraft=aircraft)
        self.report = mommy.make(FlightReport, ticket=self.ticket, engine=0)
        self.url = reverse('edit_report', args=[self.report.id])
        mommy.make(TicketRequestHistory, request=self.ticket, dt_gmt_change=12,
                   note='Test\nLine')
        support = mommy.make(Group, name='SA Support')
        analyst_user = mommy.make(User, email='analyst@sa.com')
        support_user = mommy.make(User, email='support@sa.com')
        analyst_user.groups.add(self.analyst)
        support_user.groups.add(support)

    def test_edit_report_view_not_logged_in(self):
        self.client.logout()
        result = self.client.get(self.url)
        self.assertEqual(result.url, reverse('auth_login') + '?next=' + self.url)

    def test_edit_report_view_permission_denied(self):
        self.user.user_permissions.remove(self.perm)
        result = self.client.get(self.url)
        self.assertEqual(result.url, reverse('permissions-error') + '?next=' + self.url)

    def test_edit_report_view_get_without_ticket(self):
        self.report.ticket_id=45
        self.report.save()
        result = self.client.get(self.url)
        self.assertTemplateUsed(result, 'tickets/ticket_not_public.html')

    def test_edit_report_view_get(self):
        self.ticket.user_id = None
        self.ticket.save()
        model = mommy.make(AircraftModel, twin=False)
        self.ticket.aircraft.aircraft_model = model
        self.ticket.aircraft.save()
        result = self.client.get(self.url)
        self.assertTemplateUsed(result, 'analyst/report-form.html')
        self.assertEqual(result.context['flight_forms'][0].prefix, str(self.report.engine))

    def test_edit_report_view_get_twin(self):
        sister = mommy.make(FlightReport, engine=2)
        self.report.engine = 1
        self.report.sister_report = sister
        self.report.save()
        model = mommy.make(AircraftModel, twin=True)
        self.ticket.aircraft.aircraft_model = model
        self.ticket.aircraft.save()
        result = self.client.get(self.url)
        self.assertTemplateUsed(result, 'analyst/report-form.html')
        self.assertEqual(result.context['flight_forms'][0].prefix, str(self.report.engine))
        self.assertEqual(result.context['flight_forms'][1].prefix, str(sister.engine))

    def test_edit_report_view_post_without_permission(self):
        flight = mommy.make(Flight)
        model = mommy.make(AircraftModel, twin=False)
        self.ticket.aircraft.aircraft_model = model
        self.ticket.aircraft.save()
        data = {
            '0-gami_summary': 'Satisfactory',
            '0-temperatures_summary': 'Caution',
            '0-electrical_summary': 'Alert',
            '0-engine': 0,
            '0-flight': flight.id,
        }
        result = self.client.post(self.url, data=data)
        self.assertEqual(result.url, reverse('permissions-error'))

    def test_edit_report_view_post(self):
        flight = mommy.make(Flight)
        self.report.flight = flight
        self.report.save()
        perm = mommy.make('Permission', codename='manage_sa_reports', content_type=self.content_type)
        self.user.user_permissions.add(perm)
        self.user.save()
        model = mommy.make(AircraftModel, twin=False)
        self.ticket.aircraft.aircraft_model = model
        self.ticket.aircraft.save()
        data = {
            '0-gami_summary': 'Satisfactory',
            '0-temperatures_summary': 'Caution',
            '0-electrical_summary': 'Alert',
            '0-engine': 0,
            '0-flight': flight.id,
        }
        result = self.client.post(self.url, data=data)
        self.assertTemplateUsed(result, 'analyst/report-form.html')
        self.assertEqual(result.context['pdf_download'], reverse('download_report', args=[self.report.id, flight.id, 1]))
        self.assertEqual(result.context['pdf_preview'], reverse('preview_report', args=[self.report.id, flight.id ]))

    def test_edit_report_view_post_invalid(self):
        perm = mommy.make('Permission', codename='manage_sa_reports', content_type=self.content_type)
        self.user.user_permissions.add(perm)
        self.user.save()
        model = mommy.make(AircraftModel, twin=False)
        self.ticket.aircraft.aircraft_model = model
        self.ticket.aircraft.save()
        data = {
            '0-gami_summary': 'Satisfactory',
            '0-temperatures_summary': 'Caution',
            '0-electrical_summary': 'Alert',
            '0-engine': 0,
        }
        result = self.client.post(self.url, data=data)
        self.assertIn("This field is required", str(result.context['flight_forms'][0].errors['flight']))

    def test_edit_report_view_post_twin(self):
        sister = mommy.make(FlightReport, engine=2)
        self.report.engine = 1
        self.report.sister_report = sister
        self.report.save()
        flight = mommy.make(Flight)
        self.report.flight = flight
        self.report.save()
        perm = mommy.make('Permission', codename='manage_sa_reports', content_type=self.content_type)
        self.user.user_permissions.add(perm)
        self.user.save()
        model = mommy.make(AircraftModel, twin=True)
        self.ticket.aircraft.aircraft_model = model
        self.ticket.aircraft.save()
        data = {
            '1-gami_summary': 'Satisfactory',
            '1-temperatures_summary': 'Caution',
            '1-electrical_summary': 'Alert',
            '1-engine': 0,
            '1-flight': flight.id,
            '2-gami_summary': 'Satisfactory',
            '2-temperatures_summary': 'Caution',
            '2-electrical_summary': 'Alert',
            '2-engine': 0,
            '2-flight': flight.id,
        }
        result = self.client.post(self.url, data=data)
        self.assertTemplateUsed(result, 'analyst/report-form.html')
        self.assertEqual(result.context['pdf_download'], reverse('download_report', args=[self.report.id, flight.id, 1]))


class TestGetMatchingReportFunction(TestCase):
    def test_get_matching_report_left_instance_sister_report_none(self):
        left = mommy.make(FlightReport, engine=1)
        right = mommy.make(FlightReport, engine=2)
        with self.assertRaises(Exception) as e:
            get_matching_report(left)
            self.assertEqual(e.exception, 'Not found')

    def test_get_matching_report_left_instance(self):
        ticket = mommy.make(TicketRequest)
        flight = mommy.make(Flight)
        left = mommy.make(FlightReport, engine=1, ticket=ticket, flight=flight)
        right = mommy.make(FlightReport, engine=2, flight=flight, ticket=ticket)
        l, r = get_matching_report(left)
        self.assertEqual(l ,left)
        self.assertEqual(r, right)

    def test_get_matching_report_left_instance_with_mulitiple_right_instances(self):
        ticket = mommy.make(TicketRequest)
        flight = mommy.make(Flight)
        left = mommy.make(FlightReport, engine=1, ticket=ticket, flight=flight)
        right = mommy.make(FlightReport, engine=2, flight=flight, ticket=ticket)
        mommy.make(FlightReport, engine=2, flight=flight, ticket=ticket)
        mommy.make(FlightReport, engine=2, flight=flight, ticket=ticket)
        l, r = get_matching_report(left)
        self.assertEqual(l, left)
        self.assertEqual(r, right)

    def test_get_matching_report_left_instance_with_mulitiple_right_instances_exception(self):
        ticket = mommy.make(TicketRequest)
        flight = mommy.make(Flight)
        left = mommy.make(FlightReport, id=40, engine=1, ticket=ticket, flight=flight)
        right = mommy.make(FlightReport, id=1, engine=2, flight=flight, ticket=ticket)
        mommy.make(FlightReport, id=2, engine=2, flight=flight, ticket=ticket)
        mommy.make(FlightReport, id=3, engine=2, flight=flight, ticket=ticket)
        with self.assertRaises(Exception) as e:
            get_matching_report(left)
            self.assertEqual(e.exception, 'Not found')

    def test_get_matching_report_right_instance(self):
        ticket = mommy.make(TicketRequest)
        flight = mommy.make(Flight)
        left = mommy.make(FlightReport, engine=1, ticket=ticket, flight=flight)
        right = mommy.make(FlightReport, engine=2, flight=flight, ticket=ticket, sister_report=left)
        l, r = get_matching_report(right)
        self.assertEqual(l, left)
        self.assertEqual(r, right)

    def test_get_matching_report_right_instance_no_left(self):
        ticket = mommy.make(TicketRequest)
        flight = mommy.make(Flight)
        left = mommy.make(FlightReport, engine=1)
        right = mommy.make(FlightReport, engine=2, flight=flight, ticket=ticket)
        with self.assertRaises(Exception) as e:
            get_matching_report(right)
            self.assertEqual(e.exception, 'Not found')

    def test_get_matching_report_right_instance_left(self):
        ticket = mommy.make(TicketRequest)
        flight = mommy.make(Flight)
        left = mommy.make(FlightReport, engine=1, ticket=ticket, flight=flight)
        right = mommy.make(FlightReport, engine=2, flight=flight, ticket=ticket)
        l, r = get_matching_report(right)
        self.assertEqual(l, left)
        self.assertEqual(r, right)

    def test_get_matching_report_right_instance_multiple_lefts(self):
        ticket = mommy.make(TicketRequest)
        flight = mommy.make(Flight)
        left = mommy.make(FlightReport, engine=1, ticket=ticket, flight=flight)
        right = mommy.make(FlightReport, engine=2, flight=flight, ticket=ticket)
        mommy.make(FlightReport, engine=1, flight=flight, ticket=ticket)
        mommy.make(FlightReport, engine=1, flight=flight, ticket=ticket)
        l, r = get_matching_report(right)
        self.assertEqual(l, left)
        self.assertEqual(r, right)

    def test_get_matching_report_mulitiple_instances_exception(self):
        ticket = mommy.make(TicketRequest)
        flight = mommy.make(Flight)
        left = mommy.make(FlightReport, id=40, engine=1, ticket=ticket, flight=flight)
        right = mommy.make(FlightReport, id=1, engine=2, flight=flight, ticket=ticket)
        mommy.make(FlightReport, id=2, engine=1, flight=flight, ticket=ticket)
        mommy.make(FlightReport, id=3, engine=1, flight=flight, ticket=ticket)
        with self.assertRaises(Exception) as e:
            get_matching_report(right)
            self.assertEqual(e.exception, 'Not found')
