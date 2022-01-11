# Core

# Django
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Button
from django import forms
from django.contrib.auth.models import Group
from django.urls import reverse
from django.forms import ModelForm, Select, HiddenInput, Textarea
from django.utils.datastructures import MultiValueDictKeyError

# Third-Party
from dal import autocomplete

# App
from account.models import User
from aircraft.utils import paid_aircraft_for_user
from analyst.models import FlightReport
from flights.models import FevaAlert

class FevaTicketCreateForm(forms.Form):
    subject = forms.CharField(max_length=100)
    comment = forms.CharField(max_length=30000, widget=forms.Textarea, label='Request')
    alert = forms.ModelChoiceField(queryset = FevaAlert.objects.all(), widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super(FevaTicketCreateForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        if 'initial' in kwargs and 'alert' in kwargs['initial']:
            alert_id = kwargs['initial']['alert'].id
        else:
            alert_id = self.data['alert']
        self.helper.form_action = reverse('analyst_create_feva_ticket', args=[alert_id])
        self.helper.add_input(Submit('submit', 'Create', css_class='button'))

def get_additional_notifications():
    analysts = Group.objects.get(name='Analyst').user_set.all()
    support = Group.objects.get(name='SA Support').user_set.all()
    analyst_choices = [(w.id, '{} {} '.format(w.first_name, w.last_name)) for w in analysts]
    support_choices = [(w.id, '{} {} '.format(w.first_name, w.last_name)) for w in support]
    return analyst_choices + support_choices

