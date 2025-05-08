from celery import shared_task

from api.models import CustomUser, NotificationPreference, Notification, Comment
from django.core.mail import send_mail

@shared_task
def create_notification_task(user_id, related_type, related_to_id, content, link=None):
    """
    Create a notification
    """
    Notification.objects.create(
        user_id=user_id,
        related_type=related_type,
        related_to_id=related_to_id,
        content=content,
        link=link
    )

@shared_task
def notify_mentions(mentioned_users, comment_user_username:str, comment_content:str, comment_id:int):
    """
    Inform a user that they were tagged in a particular comment
    """
    mentioned_users_obj = CustomUser.objects.filter(username__in=mentioned_users)

    if not mentioned_users_obj:
         return {"status": "failed", "error": "No recipient users were found in the database"}
    
    recipients = mentioned_users_obj.values_list('email', flat=True)
    subject = "Someone tagged you in a forum"
    message = f"The {comment_user_username} mentioned you in a comment: {comment_content[:50]}.... \n You can view it by clicking this link - <insert link here>"
    
    try:
        send_mail(subject=subject, message=message, from_email="no-reply@rashnerd.com", recipient_list=recipients)
    except Exception as e:
        print(e)
    
    notifications_created = 0
    for user in mentioned_users_obj:
        if NotificationPreference.objects.filter(user=user,notification_type=Notification.COMMENT_MENTION,enabled=False).exists():
                continue
        Notification.objects.create(
            user= user,
            related_to_id = comment_id,
            related_type = Notification.COMMENT_MENTION,
            content=f"{comment_user_username} mentioned you in a comment.",
            link="<insert-link-to-comment-or-event>"
        )
        notifications_created += 1 #Count how many notifications are created and compare with the list of recipients 
    
    return {"status": "success", "recipients": len(recipients), "notifications_created": notifications_created}

@shared_task
def notify_comment_reply(parent_comment_id: int, reply_id: int, reply_user_username: str, reply_content: str):
    """
    Create notification for the parent comment author when someone replies
    """
    try:
        parent_comment = Comment.objects.get(id=parent_comment_id)
        parent_author = parent_comment.user

        #If the parent author doesn't want to be alerted when their comment is replied then we just return
        if NotificationPreference.objects.filter(user=parent_author,notification_type=Notification.COMMENT_REPLY,enabled=False).exists():
            return
        
        # Create in-app notification
        Notification.objects.create(
            user=parent_author,
            related_to_id=reply_id,
            related_type=Notification.COMMENT_REPLY,
            content=f"{reply_user_username} replied to your comment: {reply_content[:50]}..."
        )
        
        # Send email notification
        subject = "Someone replied to your comment"
        message = f"{reply_user_username} replied to your comment: {reply_content[:50]}... \n You can view it by clicking this link - <insert link here>"
        
        send_mail(subject=subject, message=message, from_email="no-reply@rashnerd.com", recipient_list=[parent_author.email])
        
        return {"status": "success"}
    except Comment.DoesNotExist:
        return {"status": "failed", "error": "Parent comment not found"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
    
@shared_task
def notify_event_participants_of_comments(already_notified_users, comment_id:int):
    """
    Inform the participants of an event that a comment was made in the discussion forum
    """
    try:
        comment = Comment.objects.get(pk=comment_id)
    except Comment.DoesNotExist:
        return 
    
    for participant in comment.event.participants.all():
        if participant != comment.user and participant.id not in already_notified_users: 
            Notification.objects.create(
                user=participant,
                related_to_id=comment.id,
                related_type=Notification.COMMENT_ADDED,
                content=f"{comment.user.username} commented in the forum of an event you're attending: {comment.content[:50]}..."
                )


        

