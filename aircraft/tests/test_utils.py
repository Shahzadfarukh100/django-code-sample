from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from model_mommy import mommy

from account.models import User
from aircraft.utils import my_aircraft_string, paid_aircraft_for_user
from aircraft.models import Aircraft

class TestUtils(TestCase):
    def setUp(self):
        self.user = mommy.make(User, email='test@example.com')
        self.aircraft = mommy.make(Aircraft, user=self.user)

    def test_my_Aircraft_string(self):
        list = my_aircraft_string(user=self.user)
        self.assertEqual(len(list), 3)
        self.assertIn(str(self.aircraft.id), str(list))

    def test_paid_aircraft_for_user_without_user_id(self):
        list = paid_aircraft_for_user(user_id=None)
        self.assertEqual(len(list), 0)

    def test_paid_aircraft_for_user(self):
        list = paid_aircraft_for_user(user_id=self.user.id)
        self.assertEqual(len(list), 0)

    def test_paid_aircraft_for_user_analysis_pack(self):
        mommy.make('account.AnalysisPack', user=self.user, expiration_date=timezone.now() + timedelta(days=100), remaining_incidents=5)
        list = paid_aircraft_for_user(user_id=self.user.id)
        self.assertEqual(len(list), 1)
