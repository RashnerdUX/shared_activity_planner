from django.db import models
from django.conf import settings

from api.models import Event


class TaskCategory(models.Model):
    name = models.CharField(max_length=30, unique=True)
    description = models.TextField()
    is_default = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, related_name="created_task_category")
    created_for = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, related_name="custom_task_category")

    def __str__(self):
        return f"{self.name} is a task category"


class Task(models.Model):
    ACTIVE = "A"
    COMPLETED = "C"
    PENDING = "P"

    STATUS_CHOICES = [
        (ACTIVE, "Active"),
        (COMPLETED, "Completed"),
        (PENDING, "Pending")
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="tasks" )
    category = models.ForeignKey(TaskCategory, on_delete=models.PROTECT, related_name="tasks")
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, related_name="my_tasks")
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} is a task created for {self.event.title} to be done by {self.assigned_to.username}"
    
    def complete_task(self):
        if self.status == self.ACTIVE:
            self.status = self.COMPLETED
            self.save()
            return True
        return False

    def accept_task(self):
        if self.status == self.PENDING:
            self.status = self.ACTIVE
            self.save()
            return True
        return False
