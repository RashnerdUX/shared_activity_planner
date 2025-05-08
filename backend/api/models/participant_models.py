from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings

from api.models import Event, CustomUser

class Participant(models.Model):
    PENDING = "P"
    ACCEPTED = "A"
    DECLINED = "D"
    MAYBE = "M"

    RSVP_CHOICES = [
        (PENDING, "Pending"),
        (ACCEPTED, "Accepted"),
        (DECLINED, "Declined"),
        (MAYBE, "Maybe"),
    ]
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="participants")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="event_pariticipation")
    rsvp_status = models.CharField(choices=RSVP_CHOICES, default=PENDING)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["event", "user"], name="unique_participant_per_event")
        ]
        indexes = [
            models.Index(fields=["event", "user"]),
            models.Index(fields=["rsvp_status"]),
        ]
    
    def save(self, *args, **kwargs):
        # Ensure user is a member of the event's group only when the event is private
        if self.event.is_private:
            if not self.event.group.members.filter(id=self.user.id).exists():
                raise ValidationError("User must be a member of the event's group.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} is a participant in {self.event.title}"
    
    def set_rsvp_status(self, status_change):
        if self.event.status != Event.ACTIVE:
            raise ValidationError("Cannot change RSVP for non-active events.")
        
        if status_change in self.RSVP_CHOICES:
            self.rsvp_status = status_change
            self.save()
            return True
        return False
    