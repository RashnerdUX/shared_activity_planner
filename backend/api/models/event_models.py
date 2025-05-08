from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError

from .group_models import Group, GroupMember
from .location_model import Location

class Event(models.Model):
    COMPLETED = "C"
    ACTIVE = "A"
    CANCELED = "D"

    STATUS_CHOICES = [
        (COMPLETED, "Completed"),
        (ACTIVE, "Active"),
        (CANCELED, "Canceled"),
    ]

    title = models.CharField(max_length=100)
    description = models.TextField()
    creator = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="events")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="group_events")
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, related_name="event_location", null=True, blank=True)
    final_date = models.DateTimeField(null=True,)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default=ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    canceled_at = models.DateTimeField(null=True, blank=True)
    image = models.CharField(max_length=10000)
    is_private = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} was created by {self.creator.username}"
    
    def make_private(self):
        if self.status == self.ACTIVE and not self.is_private:
            self.is_private = True
            self.save()
            return True
        return False
    
    def save(self, *args, **kwargs):
        # Set is_private based on group if not explicitly set
        if self.is_private is None:
            self.is_private = self.group.is_private
        super().save(*args, **kwargs)
    
    def set_final_date(self, date_time):
        if self.status == self.ACTIVE:
            self.final_date = date_time
            self.save()
            return True
        return False
    
    def cancel(self):
        if self.status == self.ACTIVE:
            self.status = self.CANCELED
            self.canceled_at = timezone.now()
            self.save()
            return True
        return False

    def complete(self):
        if self.status == self.ACTIVE:
            self.status = self.COMPLETED
            self.save()
            return True
        return False