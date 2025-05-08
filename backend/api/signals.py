from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver, Signal


from .models import FriendsList, Notification, Comment, CustomUser, NotificationPreference
from api.tasks import notify_mentions, notify_comment_reply, notify_event_participants_of_comments

#This is a custom signal for when Comments are created
comment_created = Signal()

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_friends_profile(sender, instance, created, **kwargs):
    if created:
        FriendsList.objects.create(user=instance)

@receiver(comment_created, sender=Comment)
def handle_created_comments(sender, instance:Comment,**kwargs):
    """
    This signal handles three notification logic for the comments class.
    1. Notify a user when their comment/message has been replied to
    2. Notify a user when they are tagged in a comment
    3. Notify everyone attending the event when a new comment is added to the forum
    """
    import re

    #This is for replies notification
    if instance.parent:
            if instance.parent.user != instance.user:
                notify_comment_reply.delay(
                parent_comment_id=instance.parent.id,
                reply_id=instance.id,
                reply_user_username=instance.user.username,
                reply_content=instance.content
                )

    # This is for comment mentions notifications        
    # Check for mentions in the comment
    pattern = r'@[\w-]+'
    mentioned_users = set(u[1:] for u in re.findall(pattern, instance.content))

    if mentioned_users:
            #Ensure the users exist before going ahead
            users_to_notify_mention = CustomUser.objects.filter(username__in=mentioned_users).exclude(id=instance.user.id)

            if instance.parent and instance.parent.user in users_to_notify_mention:
                users_to_notify_mention = users_to_notify_mention.exclude(id=instance.parent.user.id)

            if users_to_notify_mention.exists():
                notify_mentions.delay(mentioned_users=users_to_notify_mention.values_list("username", flat=True), comment_user_username=instance.user, comment_content = instance.content)
    
    #This is to help event participants stay on top of what's going on by alerting them when there's a new comment in the event's forum
    if hasattr(instance, 'event') and instance.event:

        #Need to ensure that people who have been tagged to the comment or the user who was replied isn't sent another email
        already_notified_of_comment = {instance.user.id}
        
        #If this comment is a reply, exclude the parent comment user cuz he has already been notified
        if instance.parent:
            already_notified_of_comment.add(instance.parent.user.id)
        
        #If users were tagged then also exclude them from the main notification
        if 'users_to_notify_mention' in locals() and users_to_notify_mention.exists():
            for user_id in users_to_notify_mention.values_list('id', flat=True):
                already_notified_of_comment.add(user_id)

        notify_event_participants_of_comments.delay(
             already_notified_users = list(already_notified_of_comment),
             comment_id=instance.id,
        )

