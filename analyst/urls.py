# Core

# Django
from django.conf.urls import url

# App
from . import views

# Third-Party

urlpatterns = [

    # Analysis Tickets

    url(r'^analyst/generate-report/(?P<ticket_id>\d+)/(?P<flight_id>\d+)/?$',
        views.generate_report, name='generate_report'),

    url(r'^analyst/generate-report-from-paste/(?P<report_id>\d+)/(?P<ticket_id>\d+)/(?P<flight_id>\d+)/?$',
        views.paste_report, name='paste_report'),

    url(r'^analyst/edit-report/(?P<report_id>\d+)/?$',
        views.edit_report, name='edit_report'),

    url(r'^analyst/delete-report/(?P<report_id>\d*)/?$', views.delete_report, name='delete_report'),
]
