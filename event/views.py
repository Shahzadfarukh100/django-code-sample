import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, FormView, RedirectView

from conf.db import PROBLEM_ACTIVITY_STATUS, INTERNAL_EXTERNAL, PRIVATE_PUBLIC
from event.forms import EventDeleteForm
from event.forms import EventForm, EventResourceForm, EventInviteForm
from event.forms import EventUpdateForm
from event.models import Event, EventResources, EventHosts, EventOnBoardedParticipants, EventAwaitingParticipants
from event.permission_utils import has_permission_to_create_event, can_user_removed_from_event
from event.permission_utils import has_permission_to_update_event, has_permission_to_view_event_details
from event.utils import invite_user_to_event_as_host, invite_user_to_event_as_participant, send_mail_event_invitation, \
    get_public_events_qs, get_public_event_problems_qs
from event.utils import send_event_delete_email, invite_user_to_event_by_email, is_external_event, \
    send_event_attend_request_email, send_event_awaiting_participant_approved_email, \
    send_event_awaiting_participant_reject_email
from local_auth.models import User
from problem.models import Problem, ProblemEvents
from problem.utils import get_favicon_path, can_add_event_to_problem, is_trial_account, \
    add_event_hosts_to_problem_on_boarded_when_adding_event_to_problem
from problem.views import ProblemCreate, ProblemUpdateGoals, ProblemUpdate, ProblemCompetencyTagsCreate, \
    ProblemCompetencyTagsDelete, ProblemReview, ProblemEventsUpdate, ProblemEventsDelete, ProblemComplete


class EventListView(LoginRequiredMixin, ListView):
    template_name = 'event/event_list.html'
    context_object_name = 'events'

    def get_queryset(self):
        request_user = self.request.user
        event_filter = self.request.GET.get('filter', 'my_events')
        qs = Event.objects.all()

        today_date = timezone.now().date()

        qs = qs.exclude(Q(Q(private_or_public=PRIVATE_PUBLIC.PUBLIC),
                          ~Q(Q(host=request_user) | Q(on_boarded_participants=request_user)),
                          Q(date_to__lte=today_date)) |
                        Q(Q(internal_or_external=INTERNAL_EXTERNAL.INTERNAL),
                          Q(company=request_user.company),
                          ~Q(Q(host=request_user) | Q(on_boarded_participants=request_user)),
                          Q(date_to__lte=today_date)))

        if event_filter == 'my_events':
            qs = qs.filter(Q(host=request_user) | Q(on_boarded_participants=request_user))
        elif event_filter == 'company_events':
            qs = qs.filter(company=request_user.company)
        elif event_filter == 'all_events':
            qs = qs.filter(Q(host=request_user) |
                           Q(on_boarded_participants=request_user) |
                           Q(company=request_user.company) |
                           Q(internal_or_external=INTERNAL_EXTERNAL.EXTERNAL,
                             private_or_public=PRIVATE_PUBLIC.PUBLIC,
                             date_to__gte=today_date)
                           )

        qs = qs.distinct()
        qs = qs.order_by('date_from')
        return qs

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_create_event'] = has_permission_to_create_event(self.request.user)
        context['events_filter'] = self.request.GET.get('filter', 'my_events')
        context['is_trial_account'] = is_trial_account(self.request.user)
        return context


class EventCreate(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    form_class = EventForm
    template_name = 'event/event_form.html'


    def get_initial(self):
        initial = super().get_initial()
        initial['private_or_public'] = PRIVATE_PUBLIC.PRIVATE
        return initial

    def has_permission(self):
        return has_permission_to_create_event(self.request.user)

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.company = self.request.user.company
        obj.host.set([self.request.user])
        obj.save()

        return HttpResponseRedirect(reverse_lazy('events_list'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['heading'] = "Create Event"
        context['button_label'] = "Create"
        return context


class EventUpdate(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    form_class = EventUpdateForm
    template_name = 'event/event_update_form.html'
    success_url = reverse_lazy('events_list')

    def has_permission(self):
        event_id = self.kwargs.get('pk')
        return has_permission_to_update_event(self.request.user.id, event_id)

    def get_queryset(self):
        return Event.objects.filter(id__in=EventHosts.objects.filter(user=self.request.user).values_list('event_id'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['heading'] = "Update Event"
        context['button_label'] = "Update"
        context['update_view'] = True
        context['event_id'] = self.kwargs.get('pk')
        return context


class EventDetails(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    template_name = 'event/event_detail.html'
    context_object_name = 'event'

    def has_permission(self):
        event_id = self.kwargs.get('pk')
        return has_permission_to_view_event_details(self.request.user.id, event_id)

    def get_queryset(self):
        return Event.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = context['event']
        request_user_in_event_host = EventHosts.objects.filter(event=event, user=self.request.user)
        event_host_count = EventHosts.objects.filter(event=event).count()
        resources_qs = EventResources.objects.filter(event=event)


        context['event_duration_between_today'] = event.date_from <= timezone.now().date() <= event.date_to
        context['request_user_in_event_host'] = request_user_in_event_host
        context['event_host_count'] = event_host_count
        context['resources_for_event_host'] = resources_qs.filter(event=event, visible_only_to_event_host=True)
        context['resources_for_everyone'] = resources_qs.filter(event=event, visible_only_to_event_host=False)
        context['hosts'] = self.get_event_hosts(event)

        return context

    @staticmethod
    def get_event_hosts(event):
        qs =  EventHosts.objects.filter(event=event).select_related('user', 'user__company')
        return qs.order_by('-user__is_active', 'user__first_name', 'user__last_name')

    @staticmethod
    def get_event_participants(event):
        qs =  EventOnBoardedParticipants.objects.filter(event=event).select_related('user', 'user__company')
        return qs.order_by('-user__is_active', 'user__first_name', 'user__last_name')


class EventDelete(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    success_url = reverse_lazy('events_list')
    form_class = EventDeleteForm
    template_name = 'event/event_delete.html'

    def form_valid(self, form):
        cleaned_data = form.cleaned_data
        request_user = self.request.user

        if not request_user.check_password(cleaned_data.get('password')):
            form.add_error('password', 'Password is not correct')
            return self.form_invalid(form)

        event = Event.objects.get(id=self.kwargs.get('pk'))
        send_event_delete_email(event, self.request.user)
        event.delete()
        messages.info(self.request, 'event deleted successfully')

        return super().form_valid(form)

    def has_permission(self):
        event_id = self.kwargs.get('pk')
        return has_permission_to_update_event(self.request.user.id, event_id)

    def get_context_data(self, **kwargs):
        context = super(EventDelete, self).get_context_data(**kwargs)
        context['event'] = Event.objects.get(id=self.kwargs.get('pk'))
        return context
