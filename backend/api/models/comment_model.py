from django.db import models

from api.models import Event, CustomUser

class Comment(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} left this comment in the {self.event.title} discussion forum"
