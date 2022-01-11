import json
import uuid
from datetime import timedelta

from django.test import TestCase, RequestFactory
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from model_mommy import mommy
from mock import patch

from account.models import AnalysisPack, APIToken, User
from aircraft.models import (Aircraft,
                             AircraftManufacturer,
                             AircraftModel,
                             EngineManufacturer,
                             EngineModel,
                             EngineMonitorManufacturer,
                             EngineMonitorModel, UnitConversion, AircraftConversion)
from aircraft.views import (AircraftModelAutocomplete, AircraftManufacturerAutocomplete, EngineManufacturerAutocomplete,
                            EngineModelAutocomplete, EngineMonitorManufacturerAutocomplete, EngineMonitorModelAutocomplete)
from flights.models import Flight
from mx.models import MxAircraft, Contact
from mx.models import Ticket

USERNAME = 'test'
EMAIL = 'mail@example.com'
PASSWORD = 'password'
LOGIN_URL = reverse_lazy('auth_login')
PERMISSION_URL = reverse_lazy('permissions-error')
NEXT = '?next='
NOW = timezone.now()
YEAR = timedelta(days=365)


class TestAircraftListView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(EMAIL, PASSWORD)
        self.client.login(username=EMAIL, password=PASSWORD)
        self.url = reverse('aircraft_list')

    def test_aircraft_list_view_not_logged_in(self):
        self.client.logout()
        result = self.client.get(self.url)
        self.assertRedirects(result, LOGIN_URL + NEXT + self.url)

    def test_aircraft_list_view(self):
        for _ in range(2):
            mommy.make(Aircraft, user=self.user, hidden=False)
            mommy.make(Aircraft, user=self.user, hidden=True)
            mommy.make(Aircraft, hidden=False)
        result = self.client.get(self.url)
        self.assertEqual(result.status_code, 200)
        self.assertTemplateUsed(result, 'aircraft/list.html')
        aircraft = result.context['aircraft']
        self.assertEqual(aircraft.count(), 2)
        for plane in aircraft:
            self.assertEqual(plane.user, self.user)
            self.assertFalse(plane.hidden)
        self.assertTrue(result.context['no_packs'])

    def test_aircraft_list_view_no_valid_packs(self):
        mommy.make(AnalysisPack, user=self.user, expiration_date=NOW - YEAR)
        result = self.client.get(self.url)
        self.assertEqual(result.context['remaining_analyses'], 'no')

    def test_aircraft_list_view_remaining_packs(self):
        mommy.make(AnalysisPack, user=self.user, expiration_date=NOW + YEAR, remaining_incidents=5)
        mommy.make(AnalysisPack, user=self.user, expiration_date=NOW + YEAR, remaining_incidents=3)
        result = self.client.get(self.url)
        self.assertEqual(result.context['remaining_analyses'], 8)


class TestAircraftCreateView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(EMAIL, PASSWORD)
        self.client.login(username=EMAIL, password=PASSWORD)
        self.url = reverse('aircraft_create')

    def test_create_aircraft_view_not_logged_in(self):
        self.client.logout()
        result = self.client.get(self.url)
        self.assertRedirects(result, LOGIN_URL + NEXT + self.url)

    def test_create_aircraft_view(self):
        result = self.client.get(self.url)
        self.assertEqual(result.status_code, 200)
        self.assertTemplateUsed(result, 'aircraft/create.html')
        form = result.context['form']
        self.assertEqual(type(form).__name__, 'AircraftForm')

    def test_create_aircraft_view_post_form_invalid(self):
        data = {
            'registration_no': '',
            'year': '',
            'aircraft_manufacturer': '',
            'aircraft_model': '',
            'serial': '',
            'engine_manufacturer': '',
            'engine_model': '',
            'engine_monitor_manufacturer': '',
            'engine_monitor_model': '',
            'cht_warning_temperature': '',
            'cylinder_count_choices': '',
            'cylinder_count': '',
            'remarks': ''
        }
        result = self.client.post(self.url, data=data)
        self.assertEqual(result.status_code, 200)
        self.assertTemplateUsed(result, 'aircraft/create.html')
        form = result.context['form']
        self.assertFalse(form.is_valid())

    def test_create_aircraft_view_post(self):
        mfr = mommy.make(AircraftManufacturer, public=True)
        model = mommy.make(AircraftModel, public=True)
        en_mfr = mommy.make(EngineManufacturer, public=True)
        en_model = mommy.make(EngineModel, public=True)
        en_m_mfr = mommy.make(EngineMonitorManufacturer, public=True)
        en_m_model = mommy.make(EngineMonitorModel, public=True)
        data = {
            'registration_no': 'N123',
            'year': '1995',
            'aircraft_manufacturer': mfr.id,
            'aircraft_model': model.id,
            'serial': 'S123',
            'engine_manufacturer': en_mfr.id,
            'engine_model': en_model.id,
            'engine_monitor_manufacturer': en_m_mfr.id,
            'engine_monitor_model': en_m_model.id,
            'cht_warning_temperature': 60,
            'cylinder_count': '4',
            'remarks': 'Remarks'
        }
        result = self.client.post(self.url, data=data)
        self.assertRedirects(result, reverse('aircraft_list'), fetch_redirect_response=False)
        new_aircraft = Aircraft.objects.last()
        self.assertIsNotNone(new_aircraft)


class TestAircraftCreateViewFirstTime(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(EMAIL, PASSWORD)
        self.client.login(username=EMAIL, password=PASSWORD)
        self.url = reverse('aircraft_create_first_time')

    def test_create_aircraft_first_time_view_not_logged_in(self):
        self.client.logout()
        result = self.client.get(self.url)
        self.assertRedirects(result, LOGIN_URL + NEXT + self.url)

    def test_create_aircraft_first_time_view(self):
        result = self.client.get(self.url)
        self.assertEqual(result.status_code, 200)
        self.assertTemplateUsed(result, 'aircraft/create_first_time.html')
        form = result.context['form']
        self.assertEqual(type(form).__name__, 'AircraftForm')

    def test_create_aircraft_first_time_view_post_form_invalid(self):
        data = {
            'registration_no': '',
            'year': '',
            'aircraft_manufacturer': '',
            'aircraft_model': '',
            'serial': '',
            'engine_manufacturer': '',
            'engine_model': '',
            'engine_monitor_manufacturer': '',
            'engine_monitor_model': '',
            'cht_warning_temperature': '',
            'cylinder_count_choices': '',
            'cylinder_count': '',
            'remarks': ''
        }
        result = self.client.post(self.url, data=data)
        self.assertEqual(result.status_code, 200)
        self.assertTemplateUsed(result, 'aircraft/create_first_time.html')
        form = result.context['form']
        self.assertFalse(form.is_valid())

    def test_create_aircraft_first_time_view_post(self):
        mfr = mommy.make(AircraftManufacturer, public=True)
        model = mommy.make(AircraftModel, public=True)
        en_mfr = mommy.make(EngineManufacturer, public=True)
        en_model = mommy.make(EngineModel, public=True)
        en_m_mfr = mommy.make(EngineMonitorManufacturer, public=True)
        en_m_model = mommy.make(EngineMonitorModel, public=True)
        data = {
            'registration_no': 'N123',
            'year': '1995',
            'aircraft_manufacturer': mfr.id,
            'aircraft_model': model.id,
            'serial': 'S123',
            'engine_manufacturer': en_mfr.id,
            'engine_model': en_model.id,
            'engine_monitor_manufacturer': en_m_mfr.id,
            'engine_monitor_model': en_m_model.id,
            'cht_warning_temperature': 60,
            'cylinder_count': '4',
            'remarks': 'Remarks'
        }
        result = self.client.post(self.url, data=data)
        self.assertRedirects(result, reverse('files_upload'), fetch_redirect_response=False)
        new_aircraft = Aircraft.objects.last()
        self.assertIsNotNone(new_aircraft)


class TestUBG16EditView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(EMAIL, PASSWORD)
        self.client.login(username=EMAIL, password=PASSWORD)
        data = {
            'field00': 'EGT1',
            'field01': 'EGT2'
        }
        self.aircraft = mommy.make(Aircraft, user=self.user, monitor_config=json.dumps(data))
        self.url = reverse('ubg16_edit', args=[self.aircraft.id])

    def test_ubg_16_view_not_logged_in(self):
        self.client.logout()
        result = self.client.get(self.url)
        self.assertRedirects(result, LOGIN_URL + NEXT + self.url)

    def test_ubg_16_view(self):
        result = self.client.get(self.url)
        self.assertEqual(result.status_code, 200)
        self.assertTemplateUsed(result, 'aircraft/column_map_ubg16.html')
        form = result.context['form']
        self.assertEqual(type(form).__name__, 'UBG16Form')
        self.assertEqual(form.initial['field00'], 'EGT1')
        self.assertEqual(form.initial['field01'], 'EGT2')

    def test_ubg_16_view_form_invalid(self):
        data = {}
        for x in range(48):
            if x < 10:
                data['field0{}'.format(x)] = ''
            else:
                data['field'.format(x)] = ''
        data['field00'] = 'Invalid'
        result = self.client.post(self.url, data=data)
        self.assertEqual(result.status_code, 200)
        self.assertTemplateUsed(result, 'aircraft/column_map_ubg16.html')
        form = result.context['form']
        self.assertFalse(form.is_valid())

    def test_ubg_16_view_post(self):
        data = {}
        for x in range(48):
            if x < 10:
                data['field0{}'.format(x)] = ''
            else:
                data['field'.format(x)] = ''
        result = self.client.post(self.url, data=data)
        self.assertRedirects(result, reverse('aircraft_list'))

    def test_ubg_16_view_method_x(self):
        result = self.client.put(self.url)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.content, b'OK')


class TestMGLEditView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(EMAIL, PASSWORD)
        self.client.login(username=EMAIL, password=PASSWORD)
        data = {
            'field_01_00': 'EGT1',
            'field_01_01': 'EGT2'
        }
        self.aircraft = mommy.make(Aircraft, user=self.user, monitor_config=json.dumps(data))
        self.url = reverse('mgl_edit', args=[self.aircraft.id])

    def test_mgl_edit_view_not_logged_in(self):
        self.client.logout()
        result = self.client.get(self.url)
        self.assertRedirects(result, LOGIN_URL + NEXT + self.url)

    def test_mgl_edit_view(self):
        result = self.client.get(self.url)
        self.assertEqual(result.status_code, 200)
        self.assertTemplateUsed(result, 'aircraft/column_map_mgl.html')
        form = result.context['form']
        self.assertEqual(type(form).__name__, 'MGLForm')
        self.assertEqual(form.initial['field_01_00'], 'EGT1')
        self.assertEqual(form.initial['field_01_01'], 'EGT2')

    def test_mgl_edit_view_form_invalid(self):
        data = {}
        for x in range(1, 3):
            for y in range(14):
                if x < 10:
                    data['field_0{}_0{}'.format(x, y)] = ''
                else:
                    data['field_0{}_{}'.format(x, y)] = ''

        data['field_01_00'] = 'Invalid'
        result = self.client.post(self.url, data=data)
        self.assertEqual(result.status_code, 200)
        self.assertTemplateUsed(result, 'aircraft/column_map_mgl.html')
        form = result.context['form']
        self.assertFalse(form.is_valid())

    def test_mgl_edit_view_post(self):
        data = {}
        for x in range(1, 3):
            for y in range(14):
                if x < 10:
                    data['field_0{}_0{}'.format(x, y)] = ''
                else:
                    data['field_0{}_{}'.format(x, y)] = ''
        result = self.client.post(self.url, data=data)
        self.assertRedirects(result, reverse('aircraft_list'))

    def test_mgl_edit_view_method_x(self):
        result = self.client.put(self.url)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.content, b'OK')


class TestAircraftEditView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(EMAIL, PASSWORD)
        self.client.login(username=EMAIL, password=PASSWORD)
        self.aircraft = mommy.make(Aircraft, user=self.user, hidden=False)
        self.url = reverse('aircraft_edit', args=[self.aircraft.id])

    def test_aircraft_edit_view_not_logged_in(self):
        self.client.logout()
        result = self.client.get(self.url)
        self.assertRedirects(result, LOGIN_URL + NEXT + self.url)

    def test_aircraft_edit_view_not_owner(self):
        new_user = mommy.make(User)
        self.aircraft.user = new_user
        self.aircraft.save()
        result = self.client.get(self.url)
        self.assertEqual(result.status_code, 200)
        self.assertTemplateUsed(result, 'skeletons/basic.html')
        self.assertEqual(result.context['text'], 'Aircraft does not exist.')

    @patch('account.models.User.has_perm')
    def test_aircraft_edit_view_not_owner_has_perm(self, mock_perm):
        mock_perm.return_value = True
        new_user = mommy.make(User)
        self.aircraft.user = new_user
        self.aircraft.save()
        result = self.client.get(self.url)
        self.assertEqual(result.status_code, 200)
        self.assertTemplateUsed(result, 'aircraft/edit.html')

    def test_aircraft_edit_view(self):
        result = self.client.get(self.url)
        self.assertEqual(result.status_code, 200)
        self.assertTemplateUsed(result, 'aircraft/edit.html')
        self.assertEqual(result.context['aircraft_id'], str(self.aircraft.id))
        self.assertEqual(result.context['aircraft'], self.aircraft)
        self.assertFalse(result.context['mx_edit'])
        form = result.context['form']
        self.assertEqual(type(form).__name__, 'AircraftEditForm')

    def test_aircraft_edit_view_post(self):
        mfr = mommy.make(AircraftManufacturer, public=True)
        model = mommy.make(AircraftModel, public=True)
        en_mfr = mommy.make(EngineManufacturer, public=True)
        en_model = mommy.make(EngineModel, public=True)
        en_m_mfr = mommy.make(EngineMonitorManufacturer, public=True)
        en_m_model = mommy.make(EngineMonitorModel, public=True)
        data = {
            'registration_no': 'N123',
            'year': '1995',
            'aircraft_manufacturer': mfr.id,
            'aircraft_model': model.id,
            'serial': 'S123',
            'engine_manufacturer': en_mfr.id,
            'engine_model': en_model.id,
            'engine_monitor_manufacturer': en_m_mfr.id,
            'engine_monitor_model': en_m_model.id,
            'cht_warning_temperature': 60,
            'cylinder_count': '4',
            'remarks': 'Remarks'
        }
        result = self.client.post(self.url, data=data)
        self.assertRedirects(result, reverse('aircraft_list'), fetch_redirect_response=False)
        updated = Aircraft.objects.get(id=self.aircraft.id)
        self.assertEqual(updated.registration_no, data['registration_no'])
        self.assertEqual(updated.year, data['year'])
        self.assertEqual(updated.aircraft_manufacturer, mfr)
        self.assertEqual(updated.aircraft_model, model)
        self.assertEqual(updated.serial, data['serial'])
        self.assertEqual(updated.engine_manufacturer, en_mfr)
        self.assertEqual(updated.engine_model, en_model)
        self.assertEqual(updated.engine_monitor_manufacturer, en_m_mfr)
        self.assertEqual(updated.aircraft_model, model)
        self.assertEqual(updated.engine_monitor_model, en_m_model)
        self.assertEqual(updated.cht_warning_temperature, data['cht_warning_temperature'])
        self.assertEqual(updated.cylinder_count, data['cylinder_count'])
        self.assertEqual(updated.remarks, data['remarks'])

    def test_aircraft_edit_view_method_x(self):
        result = self.client.put(self.url)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.content, b'Unsupported')


class TestAircraftEditNotes(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(EMAIL, PASSWORD)
        self.client.login(username=EMAIL, password=PASSWORD)
        self.aircraft = mommy.make(Aircraft, user=self.user, hidden=False)
        self.url = reverse('aircraft_edit_notes', args=[self.aircraft.id])

    def test_aircraft_edit_notes_view_not_logged_in(self):
        self.client.logout()
        result = self.client.post(self.url)
        self.assertRedirects(result, PERMISSION_URL + NEXT + self.url, fetch_redirect_response=False)

    def test_aircraft_edit_notes_view_permission_error(self):
        result = self.client.post(self.url)
        self.assertRedirects(result, PERMISSION_URL + NEXT + self.url, fetch_redirect_response=False)

    def test_aircraft_edit_notes_view_not_post(self):
        with patch('account.models.User.has_perm') as mock_perm:
            mock_perm.return_value = True
            result = self.client.get(self.url)
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.content, b'Error')

    def test_aircraft_edit_notes_view_aircraft_does_not_exist(self):
        with patch('account.models.User.has_perm') as mock_perm:
            mock_perm.return_value = True
            result = self.client.post(reverse('aircraft_edit_notes', args=[5]))
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.content, b'Error')

    @patch('aircraft.forms.AnalystNotesForm.save')
    def test_aircraft_edit_notes_view_error(self, mock_form):
        mock_form.side_effect = Exception()
        with patch('account.models.User.has_perm') as mock_perm:
            mock_perm.return_value = True
            result = self.client.post(self.url)
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.content, b'Error')

    def test_aircraft_edit_notes_view(self):
        with patch('account.models.User.has_perm') as mock_perm:
            mock_perm.return_value = True
            result = self.client.post(self.url, {'analyst_notes': 'Notes'})
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.content, b'OK')
            updated = Aircraft.objects.get(id=self.aircraft.id)
            self.assertEqual(updated.analyst_notes, 'Notes')


class TestAircraftEditMxView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(EMAIL, PASSWORD)
        self.aircraft = mommy.make(Aircraft, user=self.user, hidden=False, registration_no='N123')
        self.ticket = mommy.make(Ticket)
        self.contact = mommy.make(Contact, email=EMAIL)
        self.mx_aircraft = mommy.make(MxAircraft,
                                      owner=self.contact,
                                      registration='N123',
                                      uuid="31deca71-d17b-4f2e-8aba-c0513b8883c7")
        self.url = reverse('aircraft_edit_mx', args=[self.aircraft.id, self.ticket.id, self.mx_aircraft.uuid])

    def test_aircraft_edit_mx_aircraft_does_not_exist(self):
        result = self.client.get(reverse('aircraft_edit_mx', args=[5, self.ticket.id, self.mx_aircraft.uuid]))
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.content, b'Aircraft not found.')

    @patch('aircraft.views.get_aircraft_from_mx_db')
    def test_aircraft_edit_mx_aircraft_multiple_mx_aircraft(self, mock_get_mx):
        mock_get_mx.side_effect = MxAircraft.MultipleObjectsReturned()
        result = self.client.get(self.url)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.content, b'Multiple or no aircraft exist for this email and registration number')

    @patch('aircraft.views.get_aircraft_from_mx_db')
    def test_aircraft_edit_mx_aircraft_access_error(self, mock_get_mx):
        mock_get_mx.return_value = mommy.make(MxAircraft, uuid=uuid.uuid4())
        result = self.client.get(self.url)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.content, b'Authentication error')

    @patch('aircraft.views.get_aircraft_from_mx_db')
    def test_aircraft_edit_mx_aircraft(self, mock_get_mx):
        mock_get_mx.return_value = self.mx_aircraft
        result = self.client.get(self.url)
        self.assertEqual(result.status_code, 200)
        self.assertTemplateUsed(result, 'aircraft/edit.html')
        form = result.context['form']
        self.assertEqual(type(form).__name__, 'AircraftEditForm')

    @patch('aircraft.views.get_aircraft_from_mx_db')
    def test_aircraft_edit_mx_aircraft_post(self, mock_get_mx):
        mock_get_mx.return_value = self.mx_aircraft
        mfr = mommy.make(AircraftManufacturer, public=True)
        model = mommy.make(AircraftModel, public=True)
        en_mfr = mommy.make(EngineManufacturer, public=True)
        en_model = mommy.make(EngineModel, public=True)
        en_m_mfr = mommy.make(EngineMonitorManufacturer, public=True)
        en_m_model = mommy.make(EngineMonitorModel, public=True)
        data = {
            'registration_no': 'N123',
            'year': '1995',
            'aircraft_manufacturer': mfr.id,
            'aircraft_model': model.id,
            'serial': 'S123',
            'engine_manufacturer': en_mfr.id,
            'engine_model': en_model.id,
            'engine_monitor_manufacturer': en_m_mfr.id,
            'engine_monitor_model': en_m_model.id,
            'cht_warning_temperature': 60,
            'cylinder_count': '4',
            'remarks': 'Remarks'
        }
        result = self.client.post(self.url, data=data)
        self.assertRedirects(result,
                             reverse('files_upload_mx', args=[self.aircraft.user.email,
                                                              self.aircraft.registration_no,
                                                              self.ticket.id,
                                                              self.mx_aircraft.uuid]),
                             fetch_redirect_response=False)
        updated = Aircraft.objects.get(id=self.aircraft.id)
        self.assertEqual(updated.registration_no, data['registration_no'])
        self.assertEqual(updated.year, data['year'])
        self.assertEqual(updated.aircraft_manufacturer, mfr)
        self.assertEqual(updated.aircraft_model, model)
        self.assertEqual(updated.serial, data['serial'])
        self.assertEqual(updated.engine_manufacturer, en_mfr)
        self.assertEqual(updated.engine_model, en_model)
        self.assertEqual(updated.engine_monitor_manufacturer, en_m_mfr)
        self.assertEqual(updated.aircraft_model, model)
        self.assertEqual(updated.engine_monitor_model, en_m_model)
        self.assertEqual(updated.cht_warning_temperature, data['cht_warning_temperature'])
        self.assertEqual(updated.cylinder_count, data['cylinder_count'])
        self.assertEqual(updated.remarks, data['remarks'])

    @patch('aircraft.views.get_aircraft_from_mx_db')
    def test_aircraft_edit_view_method_x(self, mock_get_mx):
        mock_get_mx.return_value = self.mx_aircraft
        result = self.client.put(self.url)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.content, b'Unsupported')


class TestAircraftListConversionsView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(EMAIL, PASSWORD)
        self.client.login(username=EMAIL, password=PASSWORD)
        self.aircraft = mommy.make(Aircraft, user=self.user, hidden=False)
        self.url = reverse('aircraft_list_conversions', args=[self.aircraft.id])

    def test_aircraft_list_conversions_view_not_logged_in(self):
        self.client.logout()
        result = self.client.get(self.url)
        self.assertRedirects(result, LOGIN_URL + NEXT + self.url)

    def test_aircraft_list_conversions_view_not_get(self):
        result = self.client.post(self.url)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.content, b"Not supported")

    def test_aircraft_list_conversions_view_aircraft_does_not_exist(self):
        result = self.client.get(reverse('aircraft_list_conversions', args=[5]))
        self.assertEqual(result.status_code, 200)
        self.assertTemplateUsed(result, 'skeletons/basic.html')
        self.assertEqual(result.context['text'], 'Aircraft does not exist.')

    @patch('flights.models.Flight.data')
    def test_aircraft_list_conversions_view(self, mock_data):
        for _ in range(6):
            mommy.make(Flight, aircraft=self.aircraft)
        mock_data.return_value = json.dumps({'series_data': {'EGT': 'EGT', 'D': 'Test'}})
        result = self.client.get(self.url)
        self.assertEqual(result.status_code, 200)
        self.assertTemplateUsed(result, 'aircraft/edit_measures.html')
        self.assertEqual(result.context['most_recent_flight_series'],
                         ['EGT (all cylinders)', 'CHT (all cylinders)', 'D'])

    @patch('flights.models.Flight.data')
    def test_aircraft_list_conversions_view_error(self, mock_data):
        for _ in range(6):
            mommy.make(Flight, aircraft=self.aircraft)
        mock_data.side_effect = Exception()
        result = self.client.get(self.url)
        self.assertEqual(result.status_code, 200)
        self.assertTemplateUsed(result, 'aircraft/edit_measures.html')
        self.assertIsNone(result.context['most_recent_flight_series'])


class TestAircraftAddConversion(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(EMAIL, PASSWORD)
        self.client.login(username=EMAIL, password=PASSWORD)
        self.aircraft = mommy.make(Aircraft, user=self.user, hidden=False)
        self.url = reverse('aircraft_add_conversion', args=[self.aircraft.id])

    def test_aircraft_add_conversion_view_not_logged_in(self):
        self.client.logout()
        result = self.client.post(self.url)
        self.assertRedirects(result, LOGIN_URL + NEXT + self.url)

    def test_aircraft_add_conversion_view_not_post(self):
        result = self.client.get(self.url)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.content, b"Not supported")

    def test_aircraft_add_conversion_view_aircraft_does_not_exist(self):
        result = self.client.post(reverse('aircraft_add_conversion', args=[5]))
        self.assertEqual(result.status_code, 200)
        self.assertTemplateUsed(result, 'skeletons/basic.html')
        self.assertEqual(result.context['text'], 'Aircraft does not exist.')

    def test_aircraft_add_conversion_view_form_invalid(self):
        data = {
            'series_name': '',
            'unitconversion': ''
        }
        result = self.client.post(self.url, data=data)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.content, b"Invalid form")

    def test_aircraft_add_conversion_view(self):
        unit = mommy.make(UnitConversion)
        data = {
            'series_name': 'S1234',
            'unitconversion': unit.id
        }
        result = self.client.post(self.url, data=data)
        self.assertRedirects(result, reverse('aircraft_list_conversions', args=[self.aircraft.id]),
                             fetch_redirect_response=False)
        new = AircraftConversion.objects.last()
        self.assertEqual(new.aircraft, self.aircraft)
        self.assertEqual(new.series_name, data['series_name'])
        self.assertEqual(new.unitconversion, unit)


class TestAircraftRemoveConversion(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(EMAIL, PASSWORD)
        self.client.login(username=EMAIL, password=PASSWORD)
        self.aircraft = mommy.make(Aircraft, user=self.user, hidden=False)
        self.conversion = mommy.make(AircraftConversion, aircraft=self.aircraft)
        self.url = reverse('aircraft_remove_conversion', args=[self.aircraft.id, self.conversion.id])

    def test_aircraft_remove_conversion_view_not_logged_in(self):
        self.client.logout()
        result = self.client.post(self.url)
        self.assertRedirects(result, LOGIN_URL + NEXT + self.url)

    def test_aircraft_remove_conversion_view_not_post(self):
        result = self.client.get(self.url)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.content, b"Error")

    def test_aircraft_remove_conversion_view_aircraft_does_not_exist(self):
        result = self.client.post(reverse('aircraft_remove_conversion', args=[5, self.conversion.id]))
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.content, b"Error")

    def test_aircraft_remove_conversion_view(self):
        result = self.client.post(self.url)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.content, b"OK")
        deleted = AircraftConversion.objects.filter(id=self.conversion.id)
        self.assertFalse(deleted.exists())


class TestAircraftDeleteView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(EMAIL, PASSWORD)
        self.client.login(username=EMAIL, password=PASSWORD)
        self.aircraft = mommy.make(Aircraft, user=self.user, hidden=False)
        self.url = reverse('aircraft_delete', args=[self.aircraft.id])

    def test_aircraft_delete_view_not_logged_in(self):
        self.client.logout()
        result = self.client.post(self.url)
        self.assertRedirects(result, LOGIN_URL + NEXT + self.url)

    def test_aircraft_delete_view_not_post(self):
        result = self.client.get(self.url)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.content, b"Unsupported")

    def test_aircraft_add_conversion_view_aircraft_does_not_exist(self):
        result = self.client.post(reverse('aircraft_delete', args=[5]))
        self.assertEqual(result.status_code, 200)
        self.assertTemplateUsed(result, 'skeletons/basic.html')
        self.assertEqual(result.context['text'], 'Aircraft does not exist.')

    def test_aircraft_add_conversion_view_aircraft_active_subscriptions(self):
        with patch('aircraft.models.Aircraft.current_subscription') as mock_sub:
            mock_sub.return_value = True
            result = self.client.post(self.url)
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.content, b"Cannot delete an aircraft with an active subscription.")

    def test_aircraft_add_conversion_view(self):
        result = self.client.post(self.url)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.content, b"ok")


class TestCompleteProfileView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(EMAIL, PASSWORD)
        self.client.login(username=EMAIL, password=PASSWORD)
        self.aircraft = mommy.make(Aircraft, user=self.user, hidden=False)
        self.url = reverse('complete_profile_pro', args=[self.aircraft.id])

    def test_complete_profile_view_pro_not_logged_in(self):
        self.client.logout()
        result = self.client.get(self.url)
        self.assertRedirects(result, LOGIN_URL + NEXT + self.url)

    def test_complete_profile_view_pro(self):
        result = self.client.get(self.url)
        self.assertEqual(result.status_code, 200)
        self.assertTemplateUsed(result, 'aircraft/complete.html')
        form = result.context['form']
        self.assertEqual(type(form).__name__, 'AircraftCompleteForm')

    def test_complete_profile_view_pro_method_x(self):
        result = self.client.put(self.url)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.content, b"Not supported")

    def test_complete_profile_view_pro_post(self):
        en_mfr = mommy.make(EngineManufacturer, public=True)
        en_model = mommy.make(EngineModel, public=True)
        en_m_mfr = mommy.make(EngineMonitorManufacturer, public=True)
        en_m_model = mommy.make(EngineMonitorModel, public=True)
        data = {
            'year': '1995',
            'serial': 'S123',
            'engine_manufacturer': en_mfr.id,
            'engine_model': en_model.id,
            'engine_monitor_manufacturer': en_m_mfr.id,
            'engine_monitor_model': en_m_model.id,
            'cht_warning_temperature': 60,
            'cylinder_count': '4',
            'remarks': 'Remarks'
        }
        result = self.client.post(self.url, data=data)
        self.assertRedirects(result, reverse('files_upload'), fetch_redirect_response=False)
        updated = Aircraft.objects.get(id=self.aircraft.id)
        self.assertEqual(updated.year, data['year'])
        self.assertEqual(updated.serial, data['serial'])
        self.assertEqual(updated.engine_manufacturer, en_mfr)
        self.assertEqual(updated.engine_model, en_model)
        self.assertEqual(updated.engine_monitor_model, en_m_model)
        self.assertEqual(updated.engine_monitor_manufacturer, en_m_mfr)
        self.assertEqual(updated.cht_warning_temperature, data['cht_warning_temperature'])
        self.assertEqual(updated.cylinder_count, data['cylinder_count'])
        self.assertEqual(updated.remarks, data['remarks'])

    def test_complete_profile_view_pack_post(self):
        mfr = mommy.make(AircraftManufacturer, public=True)
        model = mommy.make(AircraftModel, public=True)
        en_mfr = mommy.make(EngineManufacturer, public=True)
        en_model = mommy.make(EngineModel, public=True)
        en_m_mfr = mommy.make(EngineMonitorManufacturer, public=True)
        en_m_model = mommy.make(EngineMonitorModel, public=True)
        data = {
            'registration_no': 'N123',
            'year': '1995',
            'serial': 'S123',
            'aircraft_manufacturer': mfr.id,
            'aircraft_model': model.id,
            'engine_manufacturer': en_mfr.id,
            'engine_model': en_model.id,
            'engine_monitor_manufacturer': en_m_mfr.id,
            'engine_monitor_model': en_m_model.id,
            'cht_warning_temperature': 60,
            'cylinder_count': '4',
            'remarks': 'Remarks'
        }
        result = self.client.post(reverse('complete_profile_pack', args=[self.aircraft.id]), data=data)
        self.assertRedirects(result, reverse('files_upload'), fetch_redirect_response=False)
        updated = Aircraft.objects.get(id=self.aircraft.id)
        self.assertEqual(updated.year, data['year'])
        self.assertEqual(updated.registration_no, data['registration_no'])
        self.assertEqual(updated.serial, data['serial'])
        self.assertEqual(updated.aircraft_manufacturer, mfr)
        self.assertEqual(updated.aircraft_model, model)
        self.assertEqual(updated.engine_manufacturer, en_mfr)
        self.assertEqual(updated.engine_model, en_model)
        self.assertEqual(updated.engine_monitor_model, en_m_model)
        self.assertEqual(updated.engine_monitor_manufacturer, en_m_mfr)
        self.assertEqual(updated.cht_warning_temperature, data['cht_warning_temperature'])
        self.assertEqual(updated.cylinder_count, data['cylinder_count'])
        self.assertEqual(updated.remarks, data['remarks'])


class TestModelsViews(TestCase):
    def test_aircraft_models_view(self):
        mfr = mommy.make(AircraftManufacturer)
        for _ in range(3):
            mommy.make(AircraftModel, manufacturer=mfr, public=True)
        result = self.client.get(reverse('aircraft_models', args=[mfr.id]))
        res_data = json.loads(result.content.decode('utf-8'))
        self.assertEqual(len(res_data), 5)

    def test_engine_models_view(self):
        mfr = mommy.make(EngineManufacturer)
        for _ in range(3):
            mommy.make(EngineModel, manufacturer=mfr, public=True)
        result = self.client.get(reverse('engine_models', args=[mfr.id]))
        res_data = json.loads(result.content.decode('utf-8'))
        self.assertEqual(len(res_data), 4)

    def test_engine_monitor_models_view(self):
        mfr = mommy.make(EngineMonitorManufacturer)
        for _ in range(3):
            mommy.make(EngineMonitorModel, manufacturer=mfr, public=True)
        result = self.client.get(reverse('engine_monitor_models', args=[mfr.id]))
        res_data = json.loads(result.content.decode('utf-8'))
        self.assertEqual(len(res_data), 4)


class TestListAircraftAPIView(TestCase):
    def test_list_aircraft_api_view_not_post(self):
        result = self.client.get(reverse('list_aircraft_api'))
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.content, b"Unsupported")

    def test_list_aircraft_api_view(self):
        user = mommy.make(User)
        token = mommy.make(APIToken, user=user)
        for _ in range(2):
            mommy.make(Aircraft, user=user)
        result = self.client.post(reverse('list_aircraft_api'), data={'token': token.token})
        res_data = json.loads(result.content.decode('utf-8'))
        self.assertEqual(len(res_data), 2)


class TestAnalystViewAircraft(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(EMAIL, PASSWORD)
        self.client.login(username=EMAIL, password=PASSWORD)
        self.aircraft = mommy.make(Aircraft, user=self.user, hidden=False)
        self.url = reverse('analyst_view_aircraft', args=[self.aircraft.id])

    def test_analyst_view_aircraft_not_logged_in(self):
        self.client.logout()
        result = self.client.get(self.url)
        self.assertRedirects(result, LOGIN_URL + NEXT + self.url, fetch_redirect_response=False)

    def test_analyst_view_aircraft_permission_error(self):
        result = self.client.get(self.url)
        self.assertRedirects(result, PERMISSION_URL + NEXT + self.url, fetch_redirect_response=False)

    def test_aircraft_edit_notes_view(self):
        with patch('account.models.User.has_perm') as mock_perm:
            mock_perm.return_value = True
            result = self.client.get(self.url)
            self.assertEqual(result.status_code, 200)
            self.assertTemplateUsed(result, 'flights/list.html')


class TestAircraftManufacturerAutocomplete(TestCase):
    def setUp(self):
        self.user = mommy.make(User, email='test@example.com')
        self.aircraft_mfr = mommy.make(AircraftManufacturer, name='Test', public=True)

    def test_aircraft_manufacturer(self):
        result = self.client.get(reverse('aircraft-manufacturer-autocomplete'))
        self.assertIn(self.aircraft_mfr.name, result.content.decode('utf-8'))

    def test_aircraft_manufacturer_has_Add_permission(self):
        request = RequestFactory()
        self.assertTrue(AircraftManufacturerAutocomplete().has_add_permission(request))


class TestAicraftModelAutocomplete(TestCase):

    def setUp(self):
        self.user = mommy.make(User, email='test@example.com')
        self.aircraft_mfr = mommy.make(AircraftManufacturer, name='Test', public=True)
        self.aircraft_model = mommy.make(AircraftModel, name='model', manufacturer=self.aircraft_mfr, public=True,
                                         twin=False)

    def test_aircraft_model_autocomplete(self):
        data = {
            'forward': json.dumps({'aircraft_manufacturer': self.aircraft_mfr.id}),
            'text': '~single~Test'
        }

        result = self.client.get(reverse('aircraft-model-autocomplete'), data=data)
        data = json.loads(result.content.decode('utf-8'))['results']
        self.assertEqual(len(data), 1)

    def test_aircraft_model_autocomplete_twin(self):
        data = {
            'forward': json.dumps({'aircraft_manufacturer': self.aircraft_mfr.id, 'twin': False}),
            'text': '~twin~Te',
            'q': 'Te'
        }

        result = self.client.get(reverse('aircraft-model-autocomplete'), data=data)
        data = json.loads(result.content.decode('utf-8'))['results']
        self.assertEqual(len(data), 2)

    def test_aircraft_model_autocomplete_twin_exception(self):
        data = {
            'forward': json.dumps({'aircraft_manufacturer': 'test', 'twin': False}),
            'text': '~twin~Te',
            'q': 'Te'
        }

        result = self.client.get(reverse('aircraft-model-autocomplete'), data=data)
        data = json.loads(result.content.decode('utf-8'))['results']
        self.assertEqual(len(data), 2)

    def test_aircraft_model_autocomplete_create_object_single(self):
        text = '~single~Name'
        obj = AircraftModelAutocomplete()
        obj.forwarded = {'aircraft_manufacturer': self.aircraft_mfr.id, 'twin': False}
        obj.q = 'Te'
        obj.create_field = 'name'
        result = obj.create_object(text=text)
        self.assertEqual(result.name, 'Name')
        self.assertEqual(result.manufacturer, self.aircraft_mfr)
        self.assertEqual(result.twin, False)

    def test_aircraft_model_autocomplete_create_object_twin(self):
        text = '~twin~Name'
        obj = AircraftModelAutocomplete()
        obj.forwarded = {'aircraft_manufacturer': self.aircraft_mfr.id, 'twin': True}
        obj.q = 'Te'
        obj.create_field = 'name'
        result = obj.create_object(text=text)
        self.assertEqual(result.name, 'Name')
        self.assertEqual(result.manufacturer, self.aircraft_mfr)
        self.assertEqual(result.twin, True)

    def test_aircraft_model_autocomplete_create_object_Exception(self):
        text = '~test~Name'
        obj = AircraftModelAutocomplete()
        obj.forwarded = {'aircraft_manufacturer': self.aircraft_mfr.id, 'twin': True}
        obj.q = 'Te'
        obj.create_field = 'name'
        with self.assertRaises(Exception):
            obj.create_object(text=text)


class TestEngineManufacturerAutocomplete(TestCase):
    def setUp(self):
        self.user = mommy.make(User, email='test@example.com')
        self.engine_mfr = mommy.make(EngineManufacturer, name='Test', public=True)

    def test_engine_manufacturer(self):
        result = self.client.get(reverse('engine-manufacturer-autocomplete'))
        self.assertIn(self.engine_mfr.name, result.content.decode('utf-8'))

    def test_engine_manufacturer_has_permission(self):
        request = RequestFactory()
        self.assertTrue(EngineManufacturerAutocomplete().has_add_permission(request=request))


class TestEngineModelAutocomplete(TestCase):
    def setUp(self):
        self.emfr = mommy.make(EngineManufacturer, name='EMFR')
        self.emodel = mommy.make(EngineModel, name='EMOD', public=True, manufacturer=self.emfr)

    def test_engine_model_autocomplete_has_permission(self):
        request = RequestFactory()
        self.assertTrue(EngineModelAutocomplete().has_add_permission(request))

    def test_engine_model_autocomplete(self):
        data = {
            'forward': json.dumps({'engine_manufacturer': self.emfr.id}),
        }

        result = self.client.get(reverse('engine-model-autocomplete'), data=data)
        data = json.loads(result.content.decode('utf-8'))['results']
        self.assertEqual(len(data), 1)
        for item in data:
            self.assertEqual(item['text'], self.emodel.name)
            self.assertEqual(item['id'], u'{}'.format(self.emodel.id))

    def test_engine_model_autocomplete_exception(self):
        data = {
            'forward': json.dumps({'engine_manufacturer': 'test'}),
        }

        result = self.client.get(reverse('engine-model-autocomplete'), data=data)
        data = json.loads(result.content.decode('utf-8'))['results']
        self.assertEqual(len(data), 0)

    def test_engine_model_autocomplete_create_object(self):
        text = 'Test'
        obj = EngineModelAutocomplete()
        obj.forwarded = {'engine_manufacturer': self.emfr.id}
        obj.create_field = 'name'
        obj.q='EM'
        result = obj.create_object(text=text)
        self.assertEqual(result.name, text)
        self.assertEqual(result.manufacturer, self.emfr)


class TestEngineMonitorManfacturerAutocomplete(TestCase):
    def setUp(self):
        self.emmfr = mommy.make(EngineMonitorManufacturer, name='Test', public=True)

    def test_engine_monitor_manufacturer_autocomplete_permission(self):
        request = RequestFactory()
        self.assertTrue(EngineMonitorManufacturerAutocomplete().has_add_permission(request))

    def test_engine_monitor_manufacturer_autocomplete(self):
        data = {'q': 'tes'}
        result = self.client.get(reverse('engine-monitor-manufacturer-autocomplete'), data=data)
        res = json.loads(result.content.decode('utf-8'))['results']
        self.assertEqual(len(res), 2)


class TestEngineMonitorModelAutocomplete(TestCase):
    def setUp(self):
        self.emfr = mommy.make(EngineMonitorManufacturer, name='EMFR')
        self.emodel = mommy.make(EngineMonitorModel, name='EMonitor', public=True, manufacturer=self.emfr)

    def test_engine_monitor_model_autocomplete_has_permission(self):
        request = RequestFactory()
        self.assertTrue(EngineMonitorModelAutocomplete().has_add_permission(request))

    def test_engine_monitor_model_autocomplete(self):
        data = {
            'forward': json.dumps({'engine_monitor_manufacturer': self.emfr.id}),
            'q': 'Emo'
        }

        result = self.client.get(reverse('engine-monitor-model-autocomplete'), data=data)
        data = json.loads(result.content.decode('utf-8'))['results']
        self.assertEqual(len(data), 2)

    def test_engine_monitor_model_autocomplete_Exception(self):
        data = {
            'forward': json.dumps({'engine_monitor_manufacturer': 'test'}),
            'q': 'Emo'
        }

        result = self.client.get(reverse('engine-monitor-model-autocomplete'), data=data)
        data = json.loads(result.content.decode('utf-8'))['results']
        self.assertEqual(len(data), 1)

    def test_engine_monitor_model_autocomplete_create_object(self):
        text = 'Test'
        obj = EngineMonitorModelAutocomplete()
        obj.forwarded = {'engine_monitor_manufacturer': self.emfr.id}
        obj.create_field = 'name'
        obj.q='EM'
        result = obj.create_object(text=text)
        self.assertEqual(result.name, text)
        self.assertEqual(result.manufacturer, self.emfr)
