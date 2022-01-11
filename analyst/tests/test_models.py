from django.test import TestCase
from model_mommy import mommy
from analyst.models import FlightReport

class TestFlightReport(TestCase):
    def setUp(self):
        self.flight_report = mommy.make(FlightReport, client_comments='Satisfied')

    def test_flight_report_exists(self):
        self.assertTrue(self.flight_report.exists('client_comments'))

    def test_flight_report_not_empty(self):
        self.flight_report.findings = 'test findings'
        self.flight_report.save()
        self.assertTrue(self.flight_report.not_empty())
