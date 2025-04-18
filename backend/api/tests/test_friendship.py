from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

from ..models import CustomUser, FriendsList, FriendRequest

"""
Considering the following views mainpulate data in both the FriendsList and FriendRequestList, I decided to stick to just testing the Friendrequest list 
"""

class FriendshipTests(APITestCase):

    def setUp(self):
        self.mainuser = CustomUser.objects.create_user(
            username="Thor",
            email="Thor@asgard.com",
            password="mjolnirIsKing!!",
            first_name="Thor",
            last_name="Odinson"
        )
        self.thor_friends = FriendsList.objects.get_or_create(user=self.mainuser)
        refresh_thor = RefreshToken.for_user(self.mainuser)
        self.refreshtoken_thor = str(refresh_thor)
        self.accesstoken_thor = str(refresh_thor.access_token)

        self.otheruser = CustomUser.objects.create_user(
            username="Loki",
            email="Loki@asgard.com",
            password="th3st0riesG0d",
            first_name="Loki",
            last_name="Laufeyson"
        )
        self.loki_friends = FriendsList.objects.get_or_create(user=self.otheruser)
        refresh_loki = RefreshToken.for_user(self.otheruser)
        self.refreshtoken_loki = str(refresh_loki)
        self.accesstoken_loki = str(refresh_loki.access_token)

    def test_send_friend_request(self):
        url = reverse("send_friend_request")
        data = {"receiver_id":self.otheruser.pk, "status":"P"}

        response = self.client.post(url, data, headers={"Authorization":f"Bearer {self.accesstoken_thor}"})

        self.assertEqual(response.status_code, 200) 

    def test_accept_friend_request(self):
        send_url = reverse("send_friend_request")

        send_data = {"receiver_id":self.otheruser.pk, "status":"P"}

        send_response = self.client.post(send_url, send_data, headers={"Authorization":f"Bearer {self.accesstoken_thor}"})
        self.assertEqual(send_response.status_code, 200)

        friend_request = FriendRequest.objects.get(sender=self.mainuser,receiver=self.otheruser, status="P")
        accept_url = reverse("accept_friend_request", args=[f"{friend_request.pk}"])
        accept_data = {"id":friend_request.pk}

        accept_response = self.client.post(accept_url, accept_data,headers={"Authorization":f"Bearer {self.accesstoken_loki}"})

        #Check status of request
        self.assertEqual(accept_response.status_code, 200)
        friend_request.refresh_from_db()
        #Confirm that the status is now "Accepted"
        self.assertEqual(friend_request.status, friend_request.ACCEPTED, f"Friend request was accepted by {self.otheruser.username}")
        #Check if Thor and Loki are now in each others friend lists
        thor_friends = FriendsList.objects.get(user=self.mainuser)
        self.assertTrue(thor_friends.is_friend(self.otheruser), f"{self.mainuser.username} is not friends with {self.otheruser.username} yet")
        loki_friends = FriendsList.objects.get(user=self.otheruser)
        self.assertTrue(loki_friends.is_friend(self.mainuser), f"{self.mainuser.username} is not friends with {self.otheruser.username} yet")
    
    def test_deny_friend_request(self):
        send_url = reverse("send_friend_request")

        send_data = {"receiver_id":self.otheruser.pk, "status":"P"}

        send_response = self.client.post(send_url, send_data, headers={"Authorization":f"Bearer {self.accesstoken_thor}"})
        self.assertEqual(send_response.status_code, 200)

        friend_request = FriendRequest.objects.get(sender=self.mainuser,receiver=self.otheruser, status="P")
        deny_url = reverse("deny_friend_request", args=[f"{friend_request.pk}"])
        deny_data = {"id":friend_request.pk}

        deny_response = self.client.post(deny_url, deny_data,headers={"Authorization":f"Bearer {self.accesstoken_loki}"})

        #Check status of request
        self.assertEqual(deny_response.status_code, 200)
        #Confirm that the request is now declined
        friend_request.refresh_from_db()
        self.assertEqual(friend_request.status, friend_request.DECLINED, f"Friend request was declined by {self.otheruser.username}")
        #Check if Thor and Loki are now in each others friend lists
        thor_friends = FriendsList.objects.get(user=self.mainuser)
        self.assertFalse(thor_friends.is_friend(self.otheruser), f"{self.mainuser.username} friend request was not denied by {self.otheruser.username} yet")
        loki_friends = FriendsList.objects.get(user=self.otheruser)
        self.assertFalse(loki_friends.is_friend(self.mainuser), f"{self.otheruser.username} did not deny {self.mainuser.username} friend request")

    def test_unfriend_request(self):
        #Add Loki to Thor's friend list
        thor_friends = FriendsList.objects.get(user=self.mainuser)
        thor_friends.add_friend(self.otheruser)
        #Add Thor to Loki's friend list
        loki_friends = FriendsList.objects.get(user=self.otheruser)
        loki_friends.add_friend(self.mainuser)

        url = reverse("unfriend_user", args=[self.otheruser.pk])
        data = {"user_id":self.otheruser.pk}

        response = self.client.post(url, data, headers={"Authorization":f"Bearer {self.accesstoken_thor}"})
        self.assertEqual(response.status_code, 200)

        #Check both lists now to ensure they're no longer friends
        thor_friends.refresh_from_db()
        loki_friends.refresh_from_db()
        self.assertFalse(thor_friends.is_friend(self.otheruser), f"{self.mainuser.username} is still friends with {self.otheruser.username} yet")
        self.assertFalse(loki_friends.is_friend(self.mainuser), f"{self.otheruser.username} is still friends with {self.mainuser.username} friend request")
