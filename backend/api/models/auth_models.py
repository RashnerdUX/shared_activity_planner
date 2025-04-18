from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class CustomUser(AbstractUser):
    email = models.EmailField(
        "email address",
        unique=True,
        blank=False,  
        error_messages={
            "unique": "A user with that email already exists.",
        },
    )

    def __str__(self):
        return self.username


# Profile for users
class UserProfile(models.Model):
    #Use the same id generated when the User was created for the User's profile
    user_id = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    profile_image = models.CharField(max_length=10000)
    bio = models.TextField()
    notification_preferences = models.JSONField()
    timezone = models.CharField(max_length=100)
    default_availability = models.JSONField()

    def __str__(self):
        return f"Profile for {self.user.username}"