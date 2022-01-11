from event.models import EventHosts, EventOnBoardedParticipants


def has_permission_to_create_event(user):
    is_company_admin = user.has_perm('global_permission.is_company_admin')
    is_company_owner = user.has_perm('global_permission.is_company_owner')
    return is_company_admin or is_company_owner


def has_permission_to_update_event(user_id, event_id):
    return EventHosts.objects.filter(user_id=user_id, event_id=event_id).exists()


def has_permission_to_view_event_details(user_id, event_id):
    is_host = EventHosts.objects.filter(user_id=user_id, event_id=event_id).exists()
    is_on_boarded = EventOnBoardedParticipants.objects.filter(user_id=user_id, event_id=event_id).exists()

    return is_on_boarded or is_host


def can_user_removed_from_event(user, event):
    if EventHosts.objects.filter(event=event, user=user).exists():
        return EventHosts.objects.filter(event=event).count() > 1

    return EventOnBoardedParticipants.objects.filter(event=event, user=user).exists()
