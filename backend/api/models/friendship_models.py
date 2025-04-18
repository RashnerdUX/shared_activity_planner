from django.db import models
from django.conf import settings
from django.db.models.functions import Greatest, Least

class FriendsList(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="friends_profile", on_delete=models.CASCADE)
    friends = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="friend_connections")

    def __str__(self):
        return f"{self.user.username} has {self.friends.count()} friends"
    
    def is_friend(self, user):
        return self.friends.filter(id=user.id).exists()
    
    def add_friend(self, user):
        if user == self.user:
            return False
        if not user in self.friends.all():
            self.friends.add(user)
            return True
        return False
    
    def remove_friend(self, user):
        if user in self.friends.all():
            self.friends.remove(user)
            return True
        return False

    def unfriend(self, removee):
        #First remove from the User's friend list
        self.remove_friend(removee)

        #Then remove the user from the removee's list
        get_removee = FriendsList.objects.get(user=removee)
        get_removee.remove_friend(self.user)
        return True
    


class FriendRequest(models.Model):
    PENDING = "P"
    ACCEPTED = "A"
    DECLINED = "D"

    STATUS_UPDATE = [
    (PENDING, "Pending"),
    (ACCEPTED, "Accepted"),
    (DECLINED, "Declined"),
    ]

    sender = models.ForeignKey(settings.AUTH_USER_MODEL,related_name="sent_friend_requests",on_delete=models.CASCADE)
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL,related_name="received_friend_requests",on_delete=models.CASCADE)
    status = models.CharField(max_length=1, choices=STATUS_UPDATE, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username} wants to become friends with {self.receiver.username}"
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                Least('sender', 'receiver'),
                Greatest('sender', 'receiver'),
                condition=models.Q(status="P"),
                name="unique_pending_friend_request"
            )
        ]
    
    #To accept a request from a user, check if a request is pending then add to the Friends list of the Sender after it is accepted by the receiver
    def accept_request(self):
        if self.status == self.PENDING:
            self.status = self.ACCEPTED
            sender_friends = FriendsList.objects.get(user=self.sender)
            receiver_friends = FriendsList.objects.get(user=self.receiver)
            sender_friends.add_friend(self.receiver)
            receiver_friends.add_friend(self.sender)
            self.save()
            return True 
        return False
    
    def deny_request(self):
        if self.status == self.PENDING:
            self.status = self.DECLINED
            self.save()
            return True
        return False
    
    def revoke_request(self, sender):
        if self.status == self.PENDING and self.sender == sender:
            self.delete()
            return True
        return False