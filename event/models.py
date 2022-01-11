import uuid

from django.conf import settings
from django.db import models
from django_quill.fields import QuillField
from model_utils.models import TimeStampedModel

from accounts.models import Company
from conf.db import EVENT_TYPE, INTERNAL_EXTERNAL, PRIVATE_PUBLIC, PHYSICAL_DIGITAL


def company_event_image_file_name(instance, filename):
    return "company_{id}/event_image/{file}".format(id=instance.company.id, file=filename)


class Event(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    name = models.CharField(max_length=100)
    description = QuillField(max_length=10000)
    code = models.CharField(max_length=20, unique=True)
    one_liner_description = models.CharField(max_length=200)
    url = models.CharField(max_length=1000, null=True, blank=True)


    date_from = models.DateField()
    date_to = models.DateField()
    problem_submission_date_from = models.DateField()
    problem_submission_date_to = models.DateField()

    event_image = models.ImageField(blank=True, null=True, upload_to=company_event_image_file_name)

    host = models.ManyToManyField(settings.AUTH_USER_MODEL, through='EventHosts', related_name='hosts_event')

    event_type = models.SmallIntegerField(choices=EVENT_TYPE, default=EVENT_TYPE.CONFERENCE)
    host_has_problem_access = models.BooleanField(default=False)


    def __str__(self):
        return self.name


class EventHosts(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)

