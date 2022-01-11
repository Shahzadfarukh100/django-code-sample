# Core
# from datetime import datetime, timedelta
from datetime import timedelta, datetime

# Django

from django.test import TestCase
from account.models import User
from django.utils import timezone

# Third-Part
from model_mommy import mommy


# App
from account.models import (Subscription, SubscriptionType, User)
from aircraft.models import (Aircraft, AircraftModel, UnitConversion, AircraftConversion, EngineMonitorModel,
                             EngineMonitorManufacturer, EngineModel, EngineManufacturer)
from files.models import EngineDataFile

class AircraftTests(TestCase):

    def test_retrieving_of_current_subscription(self):
        user = mommy.make(User, email='foo@bar.com')
        aircraft = mommy.make(Aircraft, user=user)
        mommy.make(SubscriptionType, name="normal")
        current = mommy.make(Subscription, aircraft=aircraft, start_date=timezone.now() - timedelta(days=60), end_date=timezone.now() + timedelta(days=59))
        self.assertEqual(current, aircraft.current_subscription())

    def test_retrieving_of_current_subscription_when_others_exist(self):
        user = mommy.make(User, email='foo@bar.com')
        aircraft = mommy.make(Aircraft, user=user)
        mommy.make(SubscriptionType, name="normal")
        current = mommy.make(Subscription, aircraft=aircraft, start_date=timezone.now() - timedelta(days=60), end_date=timezone.now() + timedelta(days=59))
        lapsed = mommy.make(Subscription, aircraft=aircraft, start_date=timezone.now() - timedelta(days=600), end_date=timezone.now() + timedelta(days=500))
        self.assertEqual(current, aircraft.current_subscription())

    def test_retrieving_lapsed_subscription_when_current_one_exists(self):
        user = mommy.make(User, email='foo@bar.com')
        aircraft = mommy.make(Aircraft, user=user)
        mommy.make(SubscriptionType, name="normal")
        current = mommy.make(Subscription, aircraft=aircraft, start_date=timezone.now() - timedelta(days=60), end_date=timezone.now() + timedelta(days=59))
        lapsed = mommy.make(Subscription, aircraft=aircraft, start_date=timezone.now() - timedelta(days=600), end_date=timezone.now() + timedelta(days=500))
        self.assertEqual(None, aircraft.last_lapsed_subscription())

    def test_retrieving_last_lapsed_subscription(self):
        user = mommy.make(User, email='foo@bar.com')
        aircraft = mommy.make(Aircraft, user=user)
        mommy.make(SubscriptionType, name="normal")
        lapsed = mommy.make(Subscription, aircraft=aircraft, start_date=timezone.now() - timedelta(days=600), end_date=timezone.now() - timedelta(days=500))
        self.assertEqual(lapsed, aircraft.last_lapsed_subscription())

    def test_retrieving_last_lapsed_subscription_with_multiples(self):
        user = mommy.make(User, email='foo@bar.com')
        aircraft = mommy.make(Aircraft, user=user)
        mommy.make(SubscriptionType, name="normal")
        lapsed = mommy.make(Subscription, aircraft=aircraft, start_date=timezone.now() - timedelta(days=600), end_date=timezone.now() - timedelta(days=500))
        older_lapsed = mommy.make(Subscription, aircraft=aircraft, start_date=timezone.now() - timedelta(days=800), end_date=timezone.now() - timedelta(days=700))
        self.assertEqual(lapsed, aircraft.last_lapsed_subscription())

    def test_no_lapsed_subscription(self):
        user = mommy.make(User, email='foo@bar.com')
        aircraft = mommy.make(Aircraft, user=user)
        mommy.make(SubscriptionType, name="normal")
        mommy.make(Subscription, aircraft=aircraft, start_date=timezone.now() - timedelta(days=60), end_date=timezone.now() + timedelta(days=59))
        self.assertEqual(None, aircraft.last_lapsed_subscription())

    def test_aircraft_where_we_should_backdate(self):
        user = mommy.make(User, email='foo@bar.com')
        aircraft = mommy.make(Aircraft, user=user)
        mommy.make(SubscriptionType, name="normal")
        sub = mommy.make(Subscription, aircraft=aircraft, start_date=timezone.now() - timedelta(days=720), end_date=timezone.now() - timedelta(days=179))
        self.assertTrue(aircraft.should_backdate_next_subscription())

    def test_no_backdate_because_never_a_pro_subscriber(self):
        user = mommy.make(User, email='foo@bar.com')
        aircraft = mommy.make(Aircraft, user=user)
        mommy.make(SubscriptionType, name="normal")
        self.assertFalse(aircraft.should_backdate_next_subscription())

    def test_no_backdate_because_pro_subscription_too_old(self):
        user = mommy.make(User, email='foo@bar.com')
        aircraft = mommy.make(Aircraft, user=user)
        mommy.make(SubscriptionType, name="normal")
        mommy.make(Subscription, aircraft=aircraft, start_date=timezone.now() - timedelta(days=720), end_date=timezone.now() - timedelta(days=181))
        self.assertFalse(aircraft.should_backdate_next_subscription())

    def test_current_period_reports(self):
        user = mommy.make(User, email='foo@bar.com')
        model = mommy.make(AircraftModel, twin=False)
        aircraft = mommy.make(Aircraft, user=user, aircraft_model=model)
        mommy.make(SubscriptionType, name="normal")
        mommy.make(Subscription, aircraft=aircraft, start_date=timezone.now() - timedelta(days=120),
                   end_date=timezone.now() + timedelta(days=181))
        flight = mommy.make('flights.Flight', aircraft=aircraft)
        report = mommy.make('analyst.FlightReport', created_on=timezone.now() - timedelta(days=80), flight=flight)
        self.assertEqual(aircraft.current_period_reports(), 1)

    def test_current_period_reports_twin(self):
        user = mommy.make(User, email='foo@bar.com')
        model = mommy.make(AircraftModel, twin=True)
        aircraft = mommy.make(Aircraft, user=user, aircraft_model=model)
        mommy.make(SubscriptionType, name="normal")
        mommy.make(Subscription, aircraft=aircraft, start_date=timezone.now() - timedelta(days=120),
                   end_date=timezone.now() + timedelta(days=181))
        flight = mommy.make('flights.Flight', aircraft=aircraft)
        mommy.make('analyst.FlightReport', created_on=timezone.now() - timedelta(days=80), flight=flight)
        mommy.make('analyst.FlightReport', created_on=timezone.now() - timedelta(days=75), flight=flight)
        self.assertEqual(aircraft.current_period_reports(), 1)

    def test_cht_conversion_fahrenheit(self):
        user = mommy.make(User, email='foo@bar.com')
        conversion = mommy.make(UnitConversion, group_name='CHT', from_name='Fahrenheit')
        aircraft = mommy.make(Aircraft, user=user)
        mommy.make(AircraftConversion, series_name='cht', aircraft=aircraft, unitconversion=conversion)
        mommy.make(Subscription, aircraft=aircraft, start_date=timezone.now() - timedelta(days=120),
                   end_date=timezone.now() + timedelta(days=181))
        self.assertEqual(aircraft.cht_conversion_from_units(), 'F')

    def test_cht_conversion_celsius(self):
        user = mommy.make(User, email='foo@bar.com')
        conversion = mommy.make(UnitConversion, group_name='CHT', from_name='Celsius')
        aircraft = mommy.make(Aircraft, user=user)
        mommy.make(AircraftConversion, series_name='cht', aircraft=aircraft, unitconversion=conversion)
        mommy.make(Subscription, aircraft=aircraft, start_date=timezone.now() - timedelta(days=120),
                   end_date=timezone.now() + timedelta(days=181))
        self.assertEqual(aircraft.cht_conversion_from_units(), 'C')

    def test_cht_conversion_none(self):
        user = mommy.make(User, email='foo@bar.com')
        conversion = mommy.make(UnitConversion, group_name='CHT', from_name='Celsius')
        aircraft = mommy.make(Aircraft, user=user)
        mommy.make(AircraftConversion, series_name='tes', aircraft=aircraft, unitconversion=conversion)
        mommy.make(Subscription, aircraft=aircraft, start_date=timezone.now() - timedelta(days=120),
                   end_date=timezone.now() + timedelta(days=181))
        self.assertEqual(aircraft.cht_conversion_from_units(), None)

    def test_has_cht_conversion(self):
        user = mommy.make(User, email='foo@bar.com')
        conversion = mommy.make(UnitConversion, group_name='CHT', from_name='Celsius')
        aircraft = mommy.make(Aircraft, user=user)
        mommy.make(AircraftConversion, series_name='cht', aircraft=aircraft, unitconversion=conversion)
        mommy.make(Subscription, aircraft=aircraft, start_date=timezone.now() - timedelta(days=120),
                   end_date=timezone.now() + timedelta(days=181))
        self.assertTrue(aircraft.has_cht_conversion())

    def test_has_cht_conversion_not_conversions(self):
        user = mommy.make(User, email='foo@bar.com')
        conversion = mommy.make(UnitConversion, group_name='tes', from_name='Celsius')
        aircraft = mommy.make(Aircraft, user=user)
        mommy.make(AircraftConversion, series_name='tcs', aircraft=aircraft, unitconversion=conversion)
        mommy.make(Subscription, aircraft=aircraft, start_date=timezone.now() - timedelta(days=120),
                   end_date=timezone.now() + timedelta(days=181))
        self.assertFalse(aircraft.has_cht_conversion())

    def test_aircraft_delete(self):
        user = mommy.make(User, email='foo@bar.com')
        aircraft = mommy.make(Aircraft, user=user)
        file = mommy.make(EngineDataFile, aircraft=aircraft, hidden=False, processed=True)
        aircraft.delete()
        aircraft_file = EngineDataFile.all_objects.get(id=file.id)
        self.assertTrue(aircraft_file.hidden)
        self.assertTrue(aircraft.hidden)

    def test_aircraft_user_is_mx_user(self):
        user = mommy.make(User, email='foo@bar.com')
        aircraft = mommy.make(Aircraft, user=user, registration_no='N123')
        self.assertFalse(aircraft.is_current_mx_client())

    def test_should_backdate_next_subscription(self):
        user = mommy.make(User, email='foo@bar.com')
        aircraft = mommy.make(Aircraft, user=user, registration_no='N123')
        mommy.make(Subscription, aircraft=aircraft, start_date=timezone.now() - timedelta(days=120),
                   end_date=timezone.now() + timedelta(days=181))
        self.assertFalse(aircraft.should_backdate_next_subscription())

    def test_future_subscription(self):
        user = mommy.make(User, email='foo@bar.com')
        aircraft = mommy.make(Aircraft, user=user, registration_no='N123')
        sub = mommy.make(Subscription, aircraft=aircraft, start_date=timezone.now() + timedelta(days=50),
                   end_date=timezone.now() + timedelta(days=300))
        self.assertEqual(aircraft.future_subscription(), sub)

    def test_mandatory_fields(self):
        user = mommy.make(User, email='foo@bar.com')
        aircraft = mommy.make(Aircraft, user=user, registration_no='N123')
        aircraft.aircraft_model_id = 1
        aircraft.aircraft_manufacturer_id = 2
        aircraft.engine_model_id = 1
        aircraft.engine_manufacturer_id = 3
        aircraft.year = 1990
        aircraft.serial = '123'
        aircraft.engine_monitor_manufacturer_id = 4
        aircraft.engine_monitor_model_id = 1
        aircraft.save()
        self.assertTrue(aircraft.mandatory_fields_complete())


class TestModels(TestCase):

    def test_engine_manufacturer(self):
        emfr = mommy.make(EngineManufacturer, name='Test')
        self.assertEqual(emfr.__str__(), 'Test')

    def test_engine_model(self):
        model = mommy.make(EngineModel, name='Test Model')
        self.assertEqual(model.__str__(), 'Test Model')

    def test_engine_monitor_manufacturer(self):
        emm = mommy.make(EngineMonitorManufacturer, name='Monitor')
        self.assertEqual(emm.__str__(), 'Monitor')

    def test_monitor_model(self):
        emm = mommy.make(EngineMonitorModel, name='Model')
        self.assertEqual(emm.__str__(), 'Model')

    def test_unit_Conversion(self):
        conversion = mommy.make(UnitConversion, from_name='Celsius', to_name='Fahrenheit')
        self.assertEqual(conversion.__str__(), "Celsius -> Fahrenheit")
