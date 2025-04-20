from django.contrib import admin
from django.conf import settings

from api import models

# Register your models here.
admin.site.register(models.CustomUser)
admin.site.register(models.UserProfile)
admin.site.register(models.FriendRequest)
admin.site.register(models.FriendsList)
