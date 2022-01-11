from django.test import TestCase
from django.urls import reverse

from model_mommy import mommy

from account.models import User
from aircraft.forms import (AircraftSelectForm,
                            FakeAircraftSelectForm,
                            AircraftForm,
                            AircraftEditForm,
                            AircraftCompleteForm,
                            AircraftCreateSimpleForm,
                            ConversionForm,
                            AnalystNotesForm,
                            UBG16Form,
                            MGLForm)
from aircraft.models import (Aircraft, AircraftModel, EngineManufacturer,
                             EngineModel, EngineMonitorManufacturer, EngineMonitorModel,
                             UnitConversion, AircraftConversion)


class TestAircraftSelectForm(TestCase):
    def setUp(self):
        self.user = mommy.make(User, email='test@example.com')
        self.aircraft = mommy.make(Aircraft, user=self.user, hidden=False)

    def test_aircraft_select_form(self):
        form = AircraftSelectForm(user_id=self.user.id, edf_id=1)
        self.assertIn(str(self.aircraft.id), str(form.fields['aircraft_id'].choices))

    def test_aircraft_select_form_invalid(self):
        data = {'aircraft_id': 5}
        form = AircraftSelectForm(user_id=self.user.id, edf_id=1, data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("Select a valid choice. 5 is not one of the available choices", str(form.errors))

    def test_aircraft_select_form_valid(self):
        data = {'aircraft_id': self.aircraft.id}
        form = AircraftSelectForm(user_id=self.user.id, edf_id=1, data=data)
        self.assertTrue(form.is_valid())

    def test_aircraft_select_form_multiple_aircrafts(self):
        mommy.make(Aircraft, user=self.user, hidden=False)
        form = AircraftSelectForm(user_id=self.user.id, edf_id=1)
        self.assertEqual(form.fields['aircraft_id'].widget.attrs, {'class': 'need_storage'})


class TestFakeAircraftSelectForm(TestCase):
    def setUp(self):
        self.user = mommy.make(User, email='test@example.com')
        self.aircraft = mommy.make(Aircraft, user=self.user, hidden=False)

    def test_fake_aircraft_select_form(self):
        form = FakeAircraftSelectForm(aircraft=self.aircraft)
        self.assertIn(str(self.aircraft.id), str(form.fields['aircraft_id'].choices))

    def test_fake_aircraft_select_form_invalid(self):
        data = {'aircraft_id': 10}
        form = FakeAircraftSelectForm(aircraft=self.aircraft, data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("Select a valid choice. 10 is not one of the available choices", str(form.errors))

    def test_fake_aircraft_select_form_valid(self):
        data = {'aircraft_id': self.aircraft.id}
        form = FakeAircraftSelectForm(aircraft=self.aircraft, data=data)
        self.assertTrue(form.is_valid())


class TestAircraftForm(TestCase):

    def test_aircraft_form_first_time(self):
        form = AircraftForm(first_time=True)
        self.assertEqual(form.helper.form_action, reverse('aircraft_create_first_time'))

    def test_aircraft_form(self):
        form = AircraftForm()
        self.assertEqual(form.helper.form_action, reverse('aircraft_create'))

    def test_aircraft_base_form_invalid(self):
        data = {'registration_no': 'N123'}
        form = AircraftForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("This field is required", str(form.errors['cylinder_count']))

    def test_aircraft_base_form_valid(self):
        data = {'registration_no': 'N123', 'cylinder_count': 4}
        form = AircraftForm(data=data)
        self.assertTrue(form.is_valid())


class TestAircraftEditForm(TestCase):

    def setUp(self):
        self.aircraft_model = mommy.make(AircraftModel, twin=False)
        self.user = mommy.make(User, email='test@example.com')
        self.aircraft = mommy.make(Aircraft, user=self.user, hidden=False)

    def test_aircraft_edit_form(self):
        form = AircraftEditForm(aircraft_id=self.aircraft.id)
        self.assertEqual(form.helper.form_action, reverse('aircraft_edit', args=[self.aircraft.id]))

    def test_aircraft_edit_form_paid(self):
        form = AircraftEditForm(aircraft_id=self.aircraft.id, paid=True)
        self.assertTrue(form.fields['aircraft_manufacturer'].widget.attrs['disabled'])
        self.assertTrue(form.fields['aircraft_model'].widget.attrs['disabled'])
        self.assertTrue(form.fields['registration_no'].widget.attrs['readonly'])

    def test_aircraft_edit_form_has_can_edit_perm(self):
        form = AircraftEditForm(aircraft_id=self.aircraft.id,
                                paid=True,
                                has_can_edit_perm=True,
                                initial={'aircraft_model': self.aircraft_model.id},
                                mx=True,
                                ticket_id=1,
                                access_uuid='fad2334djkfjka')
        self.assertEqual(form.helper.form_action, reverse('aircraft_edit_mx', args=[self.aircraft.id, 1, 'fad2334djkfjka']))

    def test_aircraft_edit_form_post_invalid(self):
        data = {'registration_no': 'N123'}
        form = AircraftEditForm(aircraft_id=self.aircraft.id,
                                paid=True,
                                has_can_edit_perm=True,
                                initial={'aircraft_model': self.aircraft_model.id},
                                mx=True,
                                ticket_id=1,
                                access_uuid='fad2334djkfjka',
                                data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("This field is required", str(form.errors['cylinder_count']))

    def test_aircraft_edit_form_post_valid(self):
        data = {'registration_no': 'N123', 'cylinder_count': 4}
        form = AircraftEditForm(aircraft_id=self.aircraft.id,
                                paid=True,
                                has_can_edit_perm=True,
                                initial={'aircraft_model': self.aircraft_model.id},
                                mx=True,
                                ticket_id=1,
                                access_uuid='fad2334djkfjka',
                                data=data)
        self.assertTrue(form.is_valid())

    def test_aircraft_edit_form_post_different_twin(self):
        aircraft_model = mommy.make(AircraftModel, twin=True)
        self.aircraft.aircraft_model = aircraft_model
        self.aircraft.save()
        data = {'registration_no': 'N123', 'cylinder_count': 4, 'aircraft_model': self.aircraft_model.id}
        form = AircraftEditForm(aircraft_id=self.aircraft.id,
                                paid=True,
                                has_can_edit_perm=True,
                                initial={'aircraft_model': self.aircraft_model.id},
                                mx=True,
                                ticket_id=1,
                                access_uuid='fad2334djkfjka',
                                data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("You cannot change twin type to single or vice versa", str(form.errors['aircraft_model']))


class TestAircraftCompleteForm(TestCase):

    def setUp(self):
        self.user = mommy.make(User, email='test@example.com')
        self.aircraft = mommy.make(Aircraft, user=self.user, hidden=False)

    def test_aircraft_complete_form(self):
        form = AircraftCompleteForm(kind='pro', aircraft_id=self.aircraft.id)
        self.assertNotIn('registration_no', form.fields)
        self.assertNotIn('aircraft_manufacturer', form.fields)
        self.assertNotIn('aircraft_model', form.fields)
        self.assertEqual(form.helper.form_action, reverse('complete_profile_pro', args=[self.aircraft.id]))

    def test_aircraft_complete_form_pack(self):
        form = AircraftCompleteForm(kind='pack', aircraft_id=self.aircraft.id)
        self.assertIn('registration_no', form.fields)
        self.assertIn('aircraft_manufacturer', form.fields)
        self.assertIn('aircraft_model', form.fields)
        self.assertEqual(form.helper.form_action, reverse('complete_profile_pack', args=[self.aircraft.id]))

    def test_aircraft_complete_form_post_invalid(self):
        data = {'registration_no': 'N123'}
        form = AircraftCompleteForm(kind='pro', aircraft_id=self.aircraft.id, data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("This field is required", str(form.errors['cylinder_count']))
        self.assertIn("This field is required", str(form.errors['engine_manufacturer']))
        self.assertIn("This field is required", str(form.errors['engine_model']))
        self.assertIn("This field is required", str(form.errors['engine_monitor_manufacturer']))
        self.assertIn("This field is required", str(form.errors['engine_monitor_model']))

    def test_aircraft_complete_form_post_temprature_negative(self):
        data = {'registration_no': 'N123', 'cht_warning_temperature': -50}
        form = AircraftCompleteForm(kind='pro', aircraft_id=self.aircraft.id, data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('Must be positive', str(form.errors['cht_warning_temperature']))

    def test_aircraft_complete_form_post_valid(self):
        engine_mfr = mommy.make(EngineManufacturer)
        engine_model = mommy.make(EngineModel)
        engine_monitor_mfr = mommy.make(EngineMonitorManufacturer)
        engin_monitor = mommy.make(EngineMonitorModel)
        data = {'cylinder_count': 4,
                'engine_manufacturer': engine_mfr.id,
                'engine_model': engine_model.id,
                'engine_monitor_manufacturer': engine_monitor_mfr.id,
                'engine_monitor_model': engin_monitor.id}
        form = AircraftCompleteForm(kind='pro', aircraft_id=self.aircraft.id, data=data)
        self.assertTrue(form.is_valid())

    def test_aircraft_complete_form_cylinder_Count_none(self):
        engine_mfr = mommy.make(EngineManufacturer)
        engine_model = mommy.make(EngineModel)
        engine_monitor_mfr = mommy.make(EngineMonitorManufacturer)
        engin_monitor = mommy.make(EngineMonitorModel)
        data = {'cylinder_count': 'None',
                'engine_manufacturer': engine_mfr.id,
                'engine_model': engine_model.id,
                'engine_monitor_manufacturer': engine_monitor_mfr.id,
                'engine_monitor_model': engin_monitor.id}
        form = AircraftCompleteForm(kind='pro', aircraft_id=self.aircraft.id, data=data)
        self.assertTrue(form.is_valid())

class TestAircraftCreateSimpleForm(TestCase):

    def test_aircraft_create_simple_form(self):
        form = AircraftCreateSimpleForm()
        self.assertEqual(form.helper.form_action, reverse('files_upload_quick_create'))

    def test_aircraft_create_simple_form_invalid_data(self):
        data = {'remarks': 'Test remarks'}
        form = AircraftCreateSimpleForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("This field is required", str(form.errors['registration_no']))

    def test_aircraft_create_simple_form_valid_data(self):
        data = {'registration_no': 'N123'}
        form = AircraftCreateSimpleForm(data=data)
        self.assertTrue(form.is_valid())


class TestConversionForm(TestCase):

    def setUp(self):
        self.user = mommy.make(User, email='test@example.com')
        self.aircraft = mommy.make(Aircraft, user=self.user, hidden=False)
        unit = mommy.make(UnitConversion)
        self.aircraft_conversion = mommy.make(AircraftConversion, aircraft=self.aircraft, unitconversion=unit, series_name='Test')


    def test_conversion_form(self):
        form = ConversionForm(aircraft_id=self.aircraft.id)
        self.assertIn('series_name', form.fields)
        self.assertIn('unitconversion', form.fields)
        self.assertEqual(form.helper.form_action, reverse('aircraft_add_conversion', args=[self.aircraft.id]))

    def test_conversion_form_data_invalid(self):
        data = {'series_name': self.aircraft_conversion.series_name,
                'unitconversion': 'test'}
        form = ConversionForm(aircraft_id=self.aircraft.id, data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("Select a valid choice. That choice is not one of the available choices", str(form.errors['unitconversion']))

    def test_conversion_form_data_valid(self):
        data = {'series_name': self.aircraft_conversion.series_name,
                'unitconversion': self.aircraft_conversion.unitconversion.id}
        form = ConversionForm(aircraft_id=self.aircraft.id, data=data)
        self.assertTrue(form.is_valid())


class TestAnalystNotesForm(TestCase):

    def test_analyst_Notes_form_data(self):
        data = {}
        form = AnalystNotesForm(data=data)
        self.assertTrue(form.is_valid())


class TestUBG16Form(TestCase):

    def setUp(self):
        self.user = mommy.make(User, email='test@example.com')
        self.aircraft = mommy.make(Aircraft, user=self.user, hidden=False)

    def test_ubg_16_form(self):
        form = UBG16Form(aircraft_id=self.aircraft.id)
        self.assertEqual(form.helper.form_action, reverse('ubg16_edit', args=[self.aircraft.id]))

    def test_ubg_16_form_invalid(self):
        data = {
            'field00': 'test',
            'field45': 'BAT',
            'field32': 'FF',
            'field44': 'R-TIT1',
            'field47': 'L-TIT1',
            'field42': 'CHT4',
            'field22': 'L-EGT6',
            'field18': 'TEST',
            'field38': 'BAT',
        }

        form = UBG16Form(aircraft_id=self.aircraft.id, data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("Select a valid choice. test is not one of the available choices",
                      str(form.errors['field00']))
        self.assertIn("Select a valid choice. TEST is not one of the available choices",
                      str(form.errors['field18']))

    def test_ubg_16_form_valid(self):
        data = {
            'field00': 'FF',
            'field45': 'BAT',
            'field32': 'FF',
            'field44': 'R-TIT1',
            'field47': 'L-TIT1',
            'field42': 'CHT4',
            'field22': 'L-EGT6',
            'field18': 'CHT2',
            'field38': 'CHT1',
        }

        form = UBG16Form(aircraft_id=self.aircraft.id, data=data)
        self.assertTrue(form.is_valid())

class TestMGLForm(TestCase):

    def setUp(self):
        self.user = mommy.make(User, email='test@example.com')
        self.aircraft = mommy.make(Aircraft, user=self.user, hidden=False)

    def test_MGL_form(self):
        form = MGLForm(aircraft_id=self.aircraft.id)
        self.assertEqual(form.helper.form_action, reverse('mgl_edit', args=[self.aircraft.id]))

    def test_MGL_form_invalid(self):
        data = {
            'field_01_03': 'EGT1',
            'field_01_00': 'OIL_TEMP',
            'field_01_07': 'TEST',
            'field_01_11': 'R-TIT2',
            'field_01_13': 'L-TIT2',
            'field_02_05': 'CHT4',
            'field_02_03': 'TTTT',
            'field_02_10': 'TEST',
            'field_02_12': 'EGT6',
        }

        form = MGLForm(aircraft_id=self.aircraft.id, data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("Select a valid choice. TEST is not one of the available choices",
                      str(form.errors['field_01_07']))
        self.assertIn("Select a valid choice. TTTT is not one of the available choices",
                      str(form.errors['field_02_03']))

    def test_MGL_form_valid(self):
        data = {
            'field_01_03': 'EGT1',
            'field_01_00': 'OIL_TEMP',
            'field_01_07': 'EGT2',
            'field_01_11': 'R-TIT2',
            'field_01_13': 'L-TIT2',
            'field_02_05': 'CHT4',
            'field_02_03': 'L-OIL_TEMP',
            'field_02_10': 'EGT2',
            'field_02_12': 'EGT6',
        }

        form = MGLForm(aircraft_id=self.aircraft.id, data=data)
        self.assertTrue(form.is_valid())
