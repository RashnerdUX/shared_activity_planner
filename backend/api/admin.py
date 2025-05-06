from django.contrib import admin
from django.conf import settings

from api import models

# Register your models here.
admin.site.register(models.CustomUser)
admin.site.register(models.UserProfile)
admin.site.register(models.FriendRequest)
admin.site.register(models.FriendsList)
admin.site.register(models.Event)
admin.site.register(models.Group)
admin.site.register(models.GroupMember)
admin.site.register(models.Location)
admin.site.register(models.Participant)
admin.site.register(models.TimeOption)
admin.site.register(models.TimeVote)
admin.site.register(models.Comment)
