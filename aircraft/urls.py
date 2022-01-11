# Core

# Django
from django.conf.urls import url
from django.contrib.auth.decorators import login_required

# Third-Party

# App
from . import views

urlpatterns = [

    # Aircraft
    url(r'^aircraft/?$', login_required(views.AircraftListView.as_view()), name='aircraft_list'),

    # Creating and completing
    url(r'^welcome/?$',
        views.aircraft_create,
        name='aircraft_create_first_time',
        kwargs={'first_time': True}
        ),

    url(r'^add-aircraft/?$',
        views.aircraft_create,
        name='aircraft_create'),

    url(r'^pack-complete-profile/(?P<aircraft_id>\d*)/?$',
        views.complete_profile,
        {"kind": "pack"},
        name='complete_profile_pack'),

    url(r'^pro-complete-profile/(?P<aircraft_id>\d*)/?$',
        views.complete_profile,
        {"kind": "pro"},
        name='complete_profile_pro'),


]
