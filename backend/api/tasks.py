from celery import shared_task

from api.models import CustomUser
from django.core.mail import send_mail


@shared_task
def notify_mentions(mentioned_users:list, comment_user_username, comment_content):
    recipients = CustomUser.objects.filter(username__in=mentioned_users).values_list('email', flat=True)

    if not recipients:
         return {"status": "failed", "error": "No recipients were found in the database"}
    

    subject = "Someone tagged you in a forum"
    message = f"The {comment_user_username} mentioned you in a comment: {comment_content[:50]}.... \n You can view it by clicking this link - <insert link here>"
    
    try:
        send_mail(subject=subject, message=message, from_email="no-reply@rashnerd.com", recipient_list=recipients)
        return {"status": "success", "recipients": len(recipients)}
    except Exception as e:
        print(e)
        return {"status": "failed", "error": str(e)}
        
        

