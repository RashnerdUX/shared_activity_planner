from django.db import models

from api.models import CustomUser

class Notification(models.Model):
    """
    Use this to create a notification for the following resources in the database
    - Events
    - Group
    - Comments
    - Friend Requests
    - Tasks
    - Payments
    - General system announcements
    """
    #Below are the lists of notifications for the app
    EVENT_CREATED = "event_created"
    EVENT_UPDATED = "event_updated"
    EVENT_CANCELED = "event_canceled"
    EVENT_TIME_FINALIZED = "event_time_finalized"
    EVENT_INVITATION = "event_invitation"
    EVENT_REMINDER = "event_reminder"
    GROUP_CREATED = "group_created"
    GROUP_INVITATION = "group_invitation"
    GROUP_JOIN_REQUEST = "group_join_request"
    GROUP_ROLE_CHANGED = "group_role_changed"
    MESSAGE_RECEIVED = "message_received"
    COMMENT_ADDED = "comment_added"
    COMMENT_MENTION = "comment_mention"
    COMMENT_REPLY = "comment_reply"
    COMMENT_LIKED = "comment_liked"
    FRIEND_REQUEST = "friend_request"
    FRIEND_ACCEPTED = "friend_accepted"
    TASK_ASSIGNED = "task_assigned"
    SYSTEM_ANNOUNCEMENT = "system_announcement"
    #Note the two below are not active right now.
    PAYMENT_REQUESTED = "payment_requested"
    PAYMENT_RECEIVED = "payment_received"

    RELATED_TYPE_CHOICES = [
        (EVENT_CREATED, 'Event Created'),
        (EVENT_UPDATED, 'Event Updated'),
        (EVENT_CANCELED, 'Event Canceled'),
        (EVENT_TIME_FINALIZED, 'Event Time Finalized'),
        (EVENT_INVITATION, 'Event Invitation'),
        (EVENT_REMINDER, 'Event Reminder'),
        (GROUP_CREATED, 'Group Created'),
        (GROUP_INVITATION, 'Group Invitation'),
        (GROUP_JOIN_REQUEST, 'Group Join Request'),
        (GROUP_ROLE_CHANGED, 'Group Role Changed'),
        (MESSAGE_RECEIVED, 'Message Received'),
        (COMMENT_ADDED, 'Comment Added'),
        (COMMENT_MENTION, 'Mentioned in Comment'),
        (COMMENT_REPLY, 'Reply to Comment'),
        (COMMENT_LIKED, 'Comment Liked'),
        (FRIEND_REQUEST, 'Friend Request'),
        (FRIEND_ACCEPTED, 'Friend Request Accepted'),
        (TASK_ASSIGNED, 'Task Assigned'),
        (PAYMENT_REQUESTED, 'Payment Requested'),
        (PAYMENT_RECEIVED, 'Payment Received'),
        (SYSTEM_ANNOUNCEMENT, 'System Announcement'),
    ]
        
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    related_to_id = models.IntegerField() #This is dependent on the object that the user is getting a notification for
    related_type = models.CharField(max_length=50, choices=RELATED_TYPE_CHOICES)
    content = models.TextField()
    link = models.URLField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['related_type', 'related_to_id']),
        ]

    def __str__(self):
        return f"Notification to {self.user.username}"
    
    def mark_as_read(self):
        self.is_read = True
        self.save()
        return True

# models.py

class NotificationPreference(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="notification_preferences")
    notification_type = models.CharField(max_length=50, choices=Notification.RELATED_TYPE_CHOICES)
    enabled = models.BooleanField(default=True)

    class Meta:
        unique_together = ("user", "notification_type")

    def __str__(self):
        return f"{self.user.username} would like to reecive notifications pertaining to this - {self.notification_type}"

