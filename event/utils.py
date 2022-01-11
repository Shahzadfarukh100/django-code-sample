import logging
import re

from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.db.models import Q
from django.urls import reverse_lazy


from conf.db import USER_ROLE_CHOICES, INTERNAL_EXTERNAL
from event.models import EventHosts, EventOnBoardedParticipants, Event, EventAwaitingParticipants
from local_auth.models import User, LocalInvitation
from problem.models import ProblemEvents, ProblemOnBoarded, Problem

from conf.db import INTERNAL_EXTERNAL, PRIVATE_PUBLIC
from event.models import EventHosts, EventOnBoardedParticipants
from problem.models import ProblemEvents

from problem.utils import send_mail

logger = logging.getLogger(__name__)


def get_public_events_qs():
    qs = ProblemEvents.objects.filter(event__internal_or_external=INTERNAL_EXTERNAL.EXTERNAL,
                                      event__private_or_public=PRIVATE_PUBLIC.PUBLIC)

    return qs.select_related('problem', 'event')


def get_public_event_problems_qs(event_code):
    q = get_public_events_qs()
    q = q.filter(event__code=event_code)
    return Problem.objects.filter(id__in=q.values_list('problem_id', flat=True))


@shared_task()
def send_mail_event_invitation(user_id, event_id):
    user = User.objects.get(id=user_id)
    event = Event.objects.get(id=event_id)
    current_site = Site.objects.get_current()

    context = {
        'site_name': current_site.name,
        'site_url': current_site.domain,
        'event_name': event.name,
        'user': user
    }

    template = 'event/mail/event_invite.html'

    subject = f'[{current_site.name}] Event Invitation'
    to = [user.email]

    send_mail(template, context, to, subject)


def invite_existing_user_to_event_by_email(email, event, invite_type):
    try:
        user = User.objects.filter(email__iexact=email).get()
    except User.MultipleObjectsReturned:
        first_user = User.objects.filter(email__iexact=email).order_by('date_joined').first()
        User.objects.filter(email__iexact=email).exclude(id=first_user.id).delete()
        user = first_user

    try:
        if invite_type == 'host':
            invite_user_to_event_as_host(user, event)
            send_mail_event_invitation(user.id, event.id)

        if invite_type == 'participant':
            invite_user_to_event_as_participant(user, event)
            send_mail_event_invitation(user.id, event.id)

    except Exception as e:
        EventOnBoardedParticipants.objects.filter(event=event, user=user).delete()
        EventHosts.objects.filter(event=event, user=user).delete()

        logger.error(f'Error While inviting user to Event with email existing user {email}', exc_info=e)


def is_external_event(event_id):
    return Event.objects.filter(pk=event_id, internal_or_external=INTERNAL_EXTERNAL.EXTERNAL).exists()
