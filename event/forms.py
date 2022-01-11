import re

from allauth.account.forms import PasswordField
from django import forms
from django.forms import ModelForm
from multiselectfield import MultiSelectFormField

from conf.db import INTERNAL_EXTERNAL, PRIVATE_PUBLIC
from event.models import Event, EventResources, EventHosts, EventOnBoardedParticipants
from local_auth.forms import ProblemoFormMixin
from local_auth.models import User


class EventForm(ProblemoFormMixin, ModelForm):
    date_from = forms.DateField(input_formats=['%d/%m/%Y'], widget=forms.DateInput(format='%d/%m/%Y'))
    date_to = forms.DateField(input_formats=['%d/%m/%Y'], widget=forms.DateInput(format='%d/%m/%Y'))
    problem_submission_date_from = forms.DateField(input_formats=['%d/%m/%Y'], widget=forms.DateInput(format='%d/%m/%Y'))
    problem_submission_date_to = forms.DateField(input_formats=['%d/%m/%Y'], widget=forms.DateInput(format='%d/%m/%Y'))
    class Meta:
        model = Event
        fields = (
            'name',
            'description',
            'code',
            'one_liner_description',
            'url',

            'date_from',
            'date_to',
            'problem_submission_date_from',
            'problem_submission_date_to',

            'event_image',

            'event_type',
            'internal_or_external',
            'private_or_public',
            'physical_or_digital',

            'host_has_problem_access',
            'host_on_boards_members',
            'problem_owner_on_boards_members',
            'auto_accept_requests',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.format_field('name')
        self.format_field('description')
        self.format_field('code')
        self.format_field('one_liner_description')
        self.format_field('url')

        self.format_field('date_from')
        self.format_field('date_to')
        self.format_field('problem_submission_date_from')
        self.format_field('problem_submission_date_to')

        self.format_field('event_image')

        self.format_field('event_type')
        self.format_field('internal_or_external')
        self.format_field('private_or_public')
        self.format_field('physical_or_digital')

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if len(code) < 5:
            self.add_error('code', 'Event Code Must Be At least 5 Characters')

        if not re.match(r'^[A-Za-z0-9_-]+$', code):
            self.add_error('code', 'Event Code Must Contains Alphanumeric, Underscore and Hyphen')

        return code


    def validate_date(self, data):
        start = data.get('date_from')
        end = data.get('date_to')
        if start is not None and end is not None:
            if end<start:
                self.add_error('date_from', 'Event Start Date Must Be Before End Date')
                self.add_error('date_to', 'Event End Date Must Be After Start Date')

    def validate_problem_submission_date(self, data):
        start = data.get('problem_submission_date_from')
        end = data.get('problem_submission_date_to')
        if start is not None and end is not None:
            if end < start:
                self.add_error('problem_submission_date_from', 'Problem Submission Start Date Must Be Before End Date')
                self.add_error('problem_submission_date_to', 'Problem Submission End Date Must Be After Start Date')

    def validate_private_or_public(self, clean_data):
        internal_or_external = clean_data.get('internal_or_external')
        private_or_public = clean_data.get('private_or_public')
        if internal_or_external == INTERNAL_EXTERNAL.EXTERNAL and (private_or_public is None or private_or_public ==''):
            self.add_error('private_or_public', 'This field is required.')

    def validate_host_on_boards_members(self, clean_data):
        host_on_boards_members = clean_data.get('host_on_boards_members')
        problem_owner_on_boards_members = clean_data.get('problem_owner_on_boards_members')

        if host_on_boards_members is False and problem_owner_on_boards_members is False:
            self.add_error('host_on_boards_members',
                           'The event host and/or the problem owner must having onboarding permissions. Please select at least one.')

    def adjust_data(self, clean_data):
        host_has_problem_access = clean_data.get('host_has_problem_access', False)
        internal_or_external = clean_data.get('internal_or_external')
        private_or_public = clean_data.get('private_or_public')
        if internal_or_external == INTERNAL_EXTERNAL.INTERNAL:
            self.cleaned_data.update(dict(private_or_public=None))

        if not host_has_problem_access:
            self.cleaned_data.update(dict(host_on_boards_members=False))

        if internal_or_external == INTERNAL_EXTERNAL.EXTERNAL and private_or_public == PRIVATE_PUBLIC.PRIVATE:
            self.cleaned_data.update(dict(auto_accept_requests=False))

    def clean(self):
        clean_data = super().clean()
        self.validate_date(clean_data)
        self.validate_problem_submission_date(clean_data)
        self.validate_private_or_public(clean_data)
        self.validate_host_on_boards_members(clean_data)
        self.adjust_data(clean_data)


class EventUpdateForm(EventForm):
    class Meta:
        model = Event
        fields = (
            'name',
            'description',
            'one_liner_description',
            'url',

            'date_from',
            'date_to',
            'problem_submission_date_from',
            'problem_submission_date_to',

            'event_image',

            'event_type',
            'physical_or_digital',
            'auto_accept_requests',
        )

    def __init__(self, *args, **kwargs):
        super(ModelForm, self).__init__(*args, **kwargs)
        self.format_field('name')
        self.format_field('description')
        self.format_field('one_liner_description')
        self.format_field('url')

        self.format_field('date_from')
        self.format_field('date_to')
        self.format_field('problem_submission_date_from')
        self.format_field('problem_submission_date_to')

        self.format_field('event_image')

        self.format_field('event_type')
        self.format_field('physical_or_digital')
