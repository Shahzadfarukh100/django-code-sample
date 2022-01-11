"""problem URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

from event import views

urlpatterns = [
    path('public_events/<str:event_code>/', views.EventPublic.as_view(), name='event_public'),
    path('public_events/<str:event_code>/<uuid:problem_id>/', views.EventPublicProblem.as_view(), name='event_public_problem'),

    path('events/list/', views.EventListView.as_view(), name='events_list'),
    path('events/create/', views.EventCreate.as_view(), name='event_create'),
    path('events/update/<uuid:pk>/', views.EventUpdate.as_view(), name='event_update'),
    path('events/details/<uuid:pk>/', views.EventDetails.as_view(), name='event_details'),
    path('events/delete/<uuid:pk>/', views.EventDelete.as_view(), name='event_delete'),

]
