from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import Group
from model_mommy import mommy

from account.models import User
from analyst.forms import (
    FevaTicketCreateForm,
    AnalystTicketUpdateForm,
    FlightReport,
    FlightForm,
    FlightReportSearchForm,
    PostReportForm,
    PostReportAndUserForm,
    get_additional_notifications,
    FlightFormMx,
    ClientNotesForm)
from flights.models import FevaAlert
from tickets.models import TicketRequest

class TestFevaTicketCreateForm(TestCase):

    def setUp(self):
        self.alert = mommy.make(FevaAlert)

    def test_feva_ticket_create_form(self):
        form = FevaTicketCreateForm(initial={'alert': self.alert})
        self.assertEqual(form.helper.form_method, 'post')
        self.assertEqual(form.helper.form_action, reverse('analyst_create_feva_ticket', args=[self.alert.id]))

    def test_feva_ticket_create_form_data_valid(self):
        valid_data = {
            'subject': 'test',
            'comment': 'test test',
            'alert': self.alert.id
        }

        form = FevaTicketCreateForm(data=valid_data)
        self.assertTrue(form.is_valid())

    def test_feva_ticket_create_form_data_invalid(self):
        invalid_data = {
            'subject': 'test',
            'alert': 5,
        }

        form = FevaTicketCreateForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn("Select a valid choice. That choice is not one of the available choices", str(form.errors['alert']))
        self.assertIn("This field is required.", str(form.errors['comment']))


class TestAnalystTicketUpdateForm(TestCase):
    def setUp(self):
        analysits = mommy.make(Group, name='Analyst')
        supports = mommy.make(Group, name='SA Support')
        mommy.make(User, email='analyst@sa.com')
        mommy.make(User, email='support@sa.com')
        self.instance = mommy.make(TicketRequest, assigned_to_id=1, subject='test')

    def test_analyst_ticket_update_form(self):
        form = AnalystTicketUpdateForm(instance=self.instance,
                                       initial={
                                           'subject': self.instance.subject,
                                           'assignee': self.instance.assigned_to_id,
                                           'visibility': 1
                                       })

        self.assertEqual(self.instance.subject, form.initial['subject'])
        self.assertEqual(1, form.initial['visibility'])
        self.assertIn(str(self.instance.assigned_to_id), str(form.fields['assignee'].choices))

    def test_analyst_ticket_update_form_invalid(self):
        data = {
            'subject': 'test again',
            'comment': 'comment',
            'status': 'A',
            'assignee': 5
        }

        form = AnalystTicketUpdateForm(instance=self.instance,
                                       initial={
                                           'subject': self.instance.subject,
                                           'assignee': self.instance.assigned_to_id,
                                           'visibility': 1
                                       },
                                       data=data)

        self.assertIn("Select a valid choice. 5 is not one of the available choices",
                      str(form.errors['assignee']))

        self.assertIn("This field is required.", str(form.errors['visibility']))

    def test_analyst_ticket_update_form_valid(self):
        data = {
            'subject': 'test again',
            'comment': 'comment',
            'status': 'A',
            'assignee': 1,
            'visibility': 1,
        }

        form = AnalystTicketUpdateForm(instance=self.instance,
                                       initial={
                                           'subject': self.instance.subject,
                                           'assignee': self.instance.assigned_to_id,
                                           'visibility': 1
                                       },
                                       data=data)

        self.assertTrue(form.is_valid())

    def test_analyst_ticket_update_form_args(self):
        form = AnalystTicketUpdateForm({'assignee': self.instance.assigned_to_id},
                                       instance=self.instance,
                                       initial={
                                           'subject': self.instance.subject,
                                           'visibility': 1
                                       })
        self.assertIn(str(self.instance.assigned_to_id), str(form.fields['assignee'].choices))

    def test_analyst_ticket_update_form_args_multiple_values(self):
        form = AnalystTicketUpdateForm({'assignee': self.instance.assigned_to_id},{'test': 123},
                                       instance=self.instance,
                                       initial={
                                           'subject': self.instance.subject,
                                           'visibility': 1
                                       })
        self.assertNotIn(str(self.instance.assigned_to_id), str(form.fields['assignee'].choices))


class TestFlightForm(TestCase):

    def test_flight_form(self):
        form = FlightForm()
        self.assertIn('monitor1', form.fields)
        self.assertIn('ticket', form.fields)
        self.assertIn('gami2', form.fields)
        self.assertIn('power4', form.fields)
        self.assertIn('findings', form.fields)
        self.assertIn('flight', form.fields)
        self.assertIn('temperatures1', form.fields)
        self.assertNotIn('client_comments', form.fields)
        self.assertNotIn('sister_report', form.fields)
        self.assertNotIn('created_on', form.fields)

    def test_flight_form_data_invalid(self):
        data = {
            'gami_summary': 'Satisfactory',
            'temperatures_summary': 'Caution',
            'electrical_summary': 'Alert',
            'engine': 'test'
        }

        form = FlightForm(data=data)
        self.assertIn("This field is required.", str(form.errors['flight']))
        self.assertIn("Enter a whole number.", str(form.errors['engine']))

    def test_flight_form_data_valid(self):
        flight = mommy.make('flights.Flight')
        data = {
            'gami_summary': 'Satisfactory',
            'temperatures_summary': 'Caution',
            'electrical_summary': 'Alert',
            'engine': 5,
            'flight': flight.id
        }

        form = FlightForm(data=data)
        self.assertTrue(form.is_valid())


class TestFlightFormMx(TestCase):
    def test_flight_form(self):
        form = FlightFormMx()
        self.assertIn('monitor1', form.fields)
        self.assertIn('ticket', form.fields)
        self.assertIn('gami2', form.fields)
        self.assertIn('power4', form.fields)
        self.assertIn('findings', form.fields)
        self.assertIn('flight', form.fields)
        self.assertIn('temperatures1', form.fields)
        self.assertIn('client_comments', form.fields)
        self.assertNotIn('sister_report', form.fields)
        self.assertNotIn('created_on', form.fields)

    def test_flight_form_data_invalid(self):
        data = {
            'gami_summary': 'Satisfactory',
            'temperatures_summary': 'Caution',
            'electrical_summary': 'Alert',
            'engine': 'test'
        }

        form = FlightFormMx(data=data)
        self.assertIn("This field is required.", str(form.errors['flight']))
        self.assertIn("Enter a whole number.", str(form.errors['engine']))

    def test_flight_form_data_valid(self):
        flight = mommy.make('flights.Flight')
        data = {
            'gami_summary': 'Satisfactory',
            'temperatures_summary': 'Caution',
            'electrical_summary': 'Alert',
            'engine': 5,
            'flight': flight.id
        }

        form = FlightFormMx(data=data)
        self.assertTrue(form.is_valid())


class TestPostReportForm(TestCase):
    def setUp(self):
        self.user = mommy.make(User, email='test@example.com')
        self.ticket = mommy.make('tickets.TicketRequest', user=self.user)
        self.report = mommy.make(FlightReport, ticket=self.ticket)

    def test_post_report_form(self):
        form = PostReportForm(user_id=self.user.id, ticket_id=self.ticket.id, report_id=self.report.id)
        self.assertEqual(form.helper.form_action, reverse('send_report', args=[self.user.id, self.ticket.id, self.report.id]))

    def test_post_report_form_invalid(self):
        data = {
            'include_report': False,
            'include_profiles': 'test',
            'minutes': '5',
        }
        form = PostReportForm(user_id=self.user.id, ticket_id=self.ticket.id, report_id=self.report.id, data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('This field is required', str(form.errors['analyst_comments']))

    def test_post_report_form_valid(self):
        data = {
            'analyst_comments': 'Test commnets',
            'include_report': False,
            'include_profiles': 'test',
            'minutes': '5',
        }

        form = PostReportForm(user_id=self.user.id, ticket_id=self.ticket.id, report_id=self.report.id, data=data)
        self.assertTrue(form.is_valid())


class TestPostReportAndUserForm(TestCase):
    def setUp(self):
        self.user = mommy.make(User, email='test@example.com')
        self.ticket = mommy.make('tickets.TicketRequest', user=self.user)
        self.report = mommy.make(FlightReport, ticket=self.ticket)

    def test_post_report_form(self):
        form = PostReportAndUserForm(user_id=self.user.id, ticket_id=self.ticket.id, report_id=self.report.id)
        self.assertEqual(form.helper.form_action, reverse('send_report', args=[self.user.id, self.ticket.id, self.report.id]))

    def test_post_report_form_invalid(self):
        data = {
            'include_report': True,
            'include_profiles': 'test',
            'minutes': 6,
        }
        form = PostReportAndUserForm(user_id=self.user.id, ticket_id=self.ticket.id, report_id=self.report.id, data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('This field is required', str(form.errors['analyst_comments']))

    def test_post_report_form_valid(self):
        data = {
            'analyst_comments': 'Test commnets',
            'include_report': False,
            'include_profiles': 'test',
            'minutes': '5',
        }

        form = PostReportAndUserForm(user_id=self.user.id, ticket_id=self.ticket.id, report_id=self.report.id, data=data)
        self.assertTrue(form.is_valid())


class TestFlightReportSearchForm(TestCase):
    def test_flight_report_search_form(self):
        form = FlightReportSearchForm()
        self.assertEqual(form.helper.form_method, 'post')
        self.assertFalse(form.fields['ticket_id'].required)
        self.assertFalse(form.fields['last_name'].required)
        self.assertFalse(form.fields['first_name'].required)
        self.assertFalse(form.fields['aircraft_registration'].required)

    def test_flight_report_Search_form_data(self):
        data = {
            'ticket_id': 1,
            'first_name': 'test',
        }

        form = FlightReportSearchForm(data=data)
        self.assertTrue(form.is_valid())


class TestGetAdditionalNotification(TestCase):
    def setUp(self):
        analyst = mommy.make(Group, name='Analyst')
        support = mommy.make(Group, name='SA Support')
        self.user_analyst = mommy.make(User, email='analyst@sa.com')
        self.user_support = mommy.make(User, email='ssupport@sa.com')
        self.user_analyst.groups.add(analyst)
        self.user_analyst.save()
        self.user_support.groups.add(support)
        self.user_support.save()

    def test_get_Adittional_notification(self):
        result = get_additional_notifications()
        self.assertIn((self.user_support.id, '{} {} '.format(self.user_support.first_name, self.user_support.last_name)), result)
        self.assertIn((self.user_analyst.id, '{} {} '.format(self.user_analyst.first_name, self.user_analyst.last_name)), result)


class TestClientNotesForm(TestCase):
    """
    Test ClientNotesForm
    """
    def test_valid_data(self):
        valid_data = {'notes': 'test'}
        form = ClientNotesForm(data=valid_data)
        self.assertTrue(form.is_valid())

    def test_empty_data(self):
        empty_data = {'notes': None}
        form = ClientNotesForm(data=empty_data)
        self.assertTrue(form.is_valid())

    def test_invalid_data(self):
        invalid_data = {'notes': 'test' * 1000}
        form = ClientNotesForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {'notes': [u'Ensure this value has at most 1000 characters (it has 4000).']})
        self.assertEqual(form.non_field_errors(), [])
