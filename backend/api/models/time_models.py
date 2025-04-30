from django.db import models
from django.conf import settings

from api.models import Event


class TimeOption(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="time_options")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True)
    is_chosen = models.BooleanField()

    def __str__(self):
        return f"{self.start_time} is a possible option for {self.event.title}"
    
    class Meta:
        unique_together = ["event", "start_time"]
    
    def set_chosen_time(self):
        """Make a time option the chosen one for an event"""
        if not self.is_chosen and self.event.status == Event.ACTIVE:
            TimeOption.objects.filter(event=self.event, is_chosen=True).update(is_chosen=False)
            self.is_chosen = True
            self.save()
            return True
        return False
    
    def set_end_time(self, closing_time):
        """
        Not all events will have a designated ending time. So if a starting time and date has been chosen and they'd like to specify a time for closing the event then they can use this function
        Will only work if the event is active and the time option has been chosen
        """
        if self.is_chosen and self.event.status == Event.ACTIVE:
            self.end_time = closing_time
            self.save()
            return True
        return False


class TimeVote(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="time_votes")
    time_option = models.ForeignKey(TimeOption, on_delete=models.CASCADE, related_name="votes")
    voted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} chose {self.time_option.start_time} for the event - {self.time_option.event.title}"
    
    def change_vote(self, new_time):
        """
        The client can only change their vote if the event is active and no datetime has been settled on
        """
        if new_time.event != self.time_option.event:
            return False
        if self.time_option.event.status == Event.ACTIVE and not TimeOption.objects.filter(is_chosen = True, event=self.time_option.event.pk).exists():
            self.time_option = new_time
            self.save()
            return True
        return False