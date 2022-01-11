# Core
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Button
from django import forms
from django.urls import reverse
from django.forms.models import model_to_dict

# Django
from django.forms import ModelForm

# App
from aircraft.models import (
    Aircraft,
    AircraftConversion,
    AircraftManufacturer,
    AircraftModel,
    EngineManufacturer,
    EngineModel,
    EngineMonitorManufacturer,
    EngineMonitorModel,
)

# Third-Party
from dal import autocomplete, forward

REGISTRATIONNO_REGEX = r'^([A-Z0-9]{2,}|[A-Z0-9]+-[A-Z0-9]+)$'

def aircraft_for_user(user_id):
    planes = Aircraft.objects.filter(user_id = user_id, hidden=False)
    return [(p.id, p.registration_no) for p in planes]

class AircraftSelectForm(forms.Form):
    def __init__(self, *args, **kwargs):
        user_id = kwargs.pop('user_id')
        edf_id = kwargs.pop('edf_id', None)
        super(AircraftSelectForm, self).__init__(*args, **kwargs)
        choices = aircraft_for_user(user_id)
        self.fields['aircraft_id'] = forms.ChoiceField(	choices=choices, label="Data for Aircraft " )
        if len(choices) > 1:
            self.fields['aircraft_id'].widget.attrs = {'class': 'need_storage'}

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_action = reverse('file_edit', args=[edf_id])
        self.helper.form_class = 'crispy'
        self.helper.form_id = "file_edit_form"
        self.helper.add_input(Submit('submit', 'Save', css_class='button wide' ))
        self.helper.add_input(Button('cancel', "Cancel", css_class='button wide',
                                     onclick="window.location.href='{}'".format(reverse('files_list'))))


class FakeAircraftSelectForm(forms.Form):
    def __init__(self, *args, **kwargs):
        aircraft = kwargs.pop('aircraft')
        super(FakeAircraftSelectForm, self).__init__(*args, **kwargs)
        self.fields['aircraft_id'] = forms.ChoiceField(	choices=[(aircraft.id, aircraft.registration_no)], label="Data for Aircraft " )



class AircraftBaseForm(forms.Form):

    registration_no = forms.RegexField(regex=REGISTRATIONNO_REGEX)
    year = forms.CharField(max_length=4, required=False)
    aircraft_manufacturer = forms.ModelChoiceField(queryset=AircraftManufacturer.objects.filter(),
                                                   widget=autocomplete.ModelSelect2(
                                                       url='aircraft-manufacturer-autocomplete'),
                                                   required=False)
    aircraft_model = forms.ModelChoiceField(queryset=AircraftModel.objects.filter(),
                                            widget=autocomplete.ModelSelect2(url='aircraft-model-autocomplete',
                                                                             forward=['aircraft_manufacturer']),
                                            required=False)
    serial = forms.CharField(max_length=50, required=False)

    engine_manufacturer = forms.ModelChoiceField(queryset=EngineManufacturer.objects.filter(),
                                                 widget=autocomplete.ModelSelect2(
                                                     url='engine-manufacturer-autocomplete'),
                                                 required=False)
    engine_model = forms.ModelChoiceField(queryset=EngineModel.objects.filter(),
                                          widget=autocomplete.ModelSelect2(url='engine-model-autocomplete',
                                                                           forward=['engine_manufacturer']),
                                          required=False)

    engine_monitor_manufacturer = forms.ModelChoiceField(
        queryset=EngineMonitorManufacturer.objects.filter(),
        widget=autocomplete.ModelSelect2(url='engine-monitor-manufacturer-autocomplete'),
        required=False)

    engine_monitor_model = forms.ModelChoiceField(
        queryset=EngineMonitorModel.objects.filter(),
        widget=autocomplete.ModelSelect2(url='engine-monitor-model-autocomplete', forward=['engine_monitor_manufacturer']),
        required=False)

    cht_warning_temperature = forms.IntegerField(label='CHT Warning Temperature:', required=False)
    cylinder_count_choices = [(None, 'Not set'),] + Aircraft.CYLINDER_COUNT_CHOICES
    cylinder_count = forms.ChoiceField(label='Cylinders (per engine)', choices=cylinder_count_choices, required=True)
    remarks = forms.CharField(max_length=128, required=False)

    def clean_cht_warning_temperature(self):
        result = self.cleaned_data['cht_warning_temperature']
        if result is not None and result < 0:
            raise forms.ValidationError('Must be positive.')
        return result

    def clean_cylinder_count(self):
        result = self.cleaned_data['cylinder_count']
        if result is None or result == "None":
            return None
        return result
