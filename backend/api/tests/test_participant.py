from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from api.models import Group, GroupMember, Event, Participant, Location
from api.serializers import ParticipantSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.tokens import default_token_generator

CustomUser = get_user_model()

class ParticipantViewsTests(APITestCase):
    def setUp(self):
        # Create Thor user
        self.user = CustomUser.objects.create_user(
            username="Thor",
            email="Thor@asgard.com",
            password="mjolnirIsKing!!",
            first_name="Thor",
            last_name="Odinson"
        )
        self.token = default_token_generator.make_token(self.user)
        refresh = RefreshToken.for_user(self.user)
        self.refreshtoken = str(refresh)
        self.accesstoken = str(refresh.access_token)
        
        # Set up authentication
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.accesstoken}')
        
        # Create another user (Loki)
        self.other_user = CustomUser.objects.create_user(
            username="Loki",
            email="Loki@asgard.com",
            password="trickster123",
            first_name="Loki",
            last_name="Laufeyson"
        )
        
        # Create a location
        self.location = Location.objects.create(
            name="Asgard Palace",
            address="1 Valhalla Road",
            city="Asgard",
            country="Asgard",
            latitude=65.1234, 
            longitude=-10.5678, 
            details="A grand palace for Asgard's finest events, featuring golden halls and a view of the Bifrost."
        )
        
        # Create a group with Thor as creator
        self.group = Group.objects.create(
            name="Asgard Warriors",
            description="A group for Asgard's finest warriors",
            created_by=self.user,
            is_private=False
        )
        # Thor is automatically added as CREATOR
        
        # Add Loki as a member
        self.group.add_member(self.other_user)
        
        # Create an event
        self.event = Event.objects.create(
            title="Battle Training",
            description="Training session for warriors",
            creator=self.user,
            group=self.group,
            location=self.location,
            final_date=timezone.now() + timezone.timedelta(days=7),
            status=Event.ACTIVE,
            image="battle_training.jpg"
        )

    def test_list_participants(self):
        """
        Test listing participants for an event.
        """
        Participant.objects.create(event=self.event, user=self.user, rsvp_status=Participant.ACCEPTED)
        url = reverse('event_participants', kwargs={'pk': self.event.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], "Thor")
        self.assertEqual(response.data[0]['rsvp_status'], Participant.ACCEPTED)

    def test_list_participants_filter_rsvp(self):
        """
        Test filtering participants by RSVP status.
        """
        Participant.objects.create(event=self.event, user=self.user, rsvp_status=Participant.ACCEPTED)
        Participant.objects.create(event=self.event, user=self.other_user, rsvp_status=Participant.PENDING)
        url = reverse('event_participants', kwargs={'pk': self.event.id}) + '?rsvp_status=ACCEPTED'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['rsvp_status'], Participant.ACCEPTED)

    def test_list_participants_non_member(self):
        """
        Test listing participants as a non-group member.
        """
        new_user = CustomUser.objects.create_user(username="Odin", email="Odin@asgard.com", password="allfather")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(RefreshToken.for_user(new_user).access_token)}')
        url = reverse('event_participants', kwargs={'pk': self.event.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("group member", response.data['detail'])

    def test_rsvp_to_event(self):
        """
        Test RSVPing to an event (create Participant).
        """
        url = reverse('event_participants', kwargs={'pk': self.event.id})
        data = {"rsvp_status": Participant.ACCEPTED}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user'], self.user.id)
        self.assertEqual(response.data['rsvp_status'], Participant.ACCEPTED)
        self.assertTrue(Participant.objects.filter(event=self.event, user=self.user).exists())

    def test_rsvp_duplicate(self):
        """
        Test RSVPing to an event twice (updates existing Participant).
        """
        Participant.objects.create(event=self.event, user=self.user, rsvp_status=Participant.PENDING)
        url = reverse('event_participants', kwargs={'pk': self.event.id})
        data = {"rsvp_status": Participant.ACCEPTED}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['rsvp_status'], Participant.ACCEPTED)
        participant = Participant.objects.get(event=self.event, user=self.user)
        self.assertEqual(participant.rsvp_status, Participant.ACCEPTED)

    def test_rsvp_non_active_event(self):
        """
        Test RSVPing to a non-active event.
        """
        self.event.cancel()
        self.event.save()
        url = reverse('event_participants', kwargs={'pk': self.event.id})
        data = {"rsvp_status": Participant.ACCEPTED}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non-active event", response.data['non_field_errors'][0])

    def test_update_rsvp_status(self):
        """
        Test updating RSVP status.
        """
        Participant.objects.create(event=self.event, user=self.user, rsvp_status=Participant.PENDING)
        url = reverse('event_participants', kwargs={'pk': self.event.id})
        data = {"rsvp_status": Participant.DECLINED}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['rsvp_status'], Participant.DECLINED)
        participant = Participant.objects.get(event=self.event, user=self.user)
        self.assertEqual(participant.rsvp_status, Participant.DECLINED)

    def test_update_rsvp_non_participant(self):
        """
        Test updating RSVP for a non-participant.
        """
        url = reverse('event_participants', kwargs={'pk': self.event.id})
        data = {"rsvp_status": Participant.ACCEPTED}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_remove_rsvp(self):
        """
        Test removing an RSVP.
        """
        Participant.objects.create(event=self.event, user=self.user, rsvp_status=Participant.ACCEPTED)
        url = reverse('event_participants', kwargs={'pk': self.event.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Participant.objects.filter(event=self.event, user=self.user).exists())

    def test_invite_group_member(self):
        """
        Test inviting a group member to an event.
        """
        url = reverse('send_invites', kwargs={'pk': self.event.id})
        data = {"user_ids": [self.other_user.id]}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['created']), 1)
        self.assertEqual(response.data['created'][0]['user'], self.other_user.id)
        self.assertEqual(response.data['created'][0]['rsvp_status'], Participant.PENDING)
        self.assertTrue(Participant.objects.filter(event=self.event, user=self.other_user).exists())

    def test_invite_multiple_users(self):
        """
        Test inviting multiple users, including some errors.
        """
        new_user = CustomUser.objects.create_user(username="Odin", email="Odin@asgard.com", password="allfather")
        new_user2 = CustomUser.objects.create_user(username="Freya", email="Freya@asgard.com", password="allmother")
        url = reverse('send_invites', kwargs={'pk': self.event.id})
        data = {"user_ids": [self.other_user.id, new_user.id, new_user2.id, 999]}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_207_MULTI_STATUS)
        self.assertEqual(len(response.data['created']), 3)
        self.assertEqual(response.data['created'][0]['user'], self.other_user.id)
        self.assertEqual(len(response.data['errors']), 1)
        self.assertNotIn("not a group member", response.data['errors'][0])
        self.assertIn("not found", response.data['errors'][0])
        self.assertTrue(Participant.objects.filter(event=self.event, user=self.other_user).exists())
        self.assertTrue(Participant.objects.filter(event=self.event, user=new_user).exists())

    def test_invite_already_participant(self):
        """
        Test inviting a user who is already a participant.
        """
        Participant.objects.create(event=self.event, user=self.other_user, rsvp_status=Participant.ACCEPTED)
        url = reverse('send_invites', kwargs={'pk': self.event.id})
        data = {"user_ids": [self.other_user.id]}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already a participant", response.data['errors'][0])

    def test_invite_non_admin(self):
        """
        Test inviting as a non-admin/non-creator.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(RefreshToken.for_user(self.other_user).access_token)}')
        url = reverse('send_invites', kwargs={'pk': self.event.id})
        data = {"user_ids": [self.user.id]}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("admins or creators", response.data['detail'])

    def test_invite_unauthenticated(self):
        """
        Test inviting without authentication.
        """
        self.client.credentials()
        url = reverse('send_invites', kwargs={'pk': self.event.id})
        data = {"user_ids": [self.other_user.id]}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)