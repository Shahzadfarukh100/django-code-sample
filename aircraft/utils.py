# Core

# Django

# App
from account.models import User
from aircraft.models import Aircraft

# Third-Party

def paid_aircraft_for_user(user_id):

    planes = Aircraft.objects.filter(user_id = user_id, hidden=False)

    # If we have pack, then all aircraft are good.
    if user_id is None:
        have_pack = False
    else:
        user = User.objects.get(id=user_id)
        if user is not None and user.oldest_valid_pack() is not None:
            have_pack = True
        else:
            have_pack = False

    ret = []
    for p in planes:
        if have_pack or p.current_subscription() is not None:
            ret.append((p.id, p.registration_no))
    return ret


def my_aircraft_string(user):
    my_aircraft = Aircraft.objects.filter(user=user).values_list('id')
    clean_aircraft = []
    for a in my_aircraft:
        clean_aircraft.append(a[0])

    if len(clean_aircraft) < 2:
        clean_aircraft.append(-1)
        clean_aircraft.append(-1)
    return clean_aircraft
