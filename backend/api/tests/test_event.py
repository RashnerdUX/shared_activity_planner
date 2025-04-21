from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from api.models import Group, GroupMember, Event, Location
from api.serializers import EventSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.tokens import default_token_generator
import datetime

CustomUser = get_user_model()

class EventViewsTests(APITestCase):
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
        
        # Create another user (Loki) for testing
        self.other_user = CustomUser.objects.create_user(
            username="Loki",
            email="Loki@asgard.com",
            password="trickster123",
            first_name="Loki",
            last_name="Laufeyson"
        )
        
        # Create a location
        # TODO: Edit this to create a Location object according to my implementation later
        self.location = Location.objects.create(
            name="Asgard Palace",
            address="1 Valhalla Road",
            city="Asgard",
            country="Asgard"
        )
        
        # Create a group with Thor as creator
        self.group = Group.objects.create(
            name="Asgard Warriors",
            description="A group for Asgard's finest warriors",
            created_by=self.user,
            is_private=False
        )
        # Thor is automatically added as CREATOR via Group.save()
        
        # Add Loki as a regular member
        self.group.add_member(self.other_user)
        
        # Create a test event
        self.event = Event.objects.create(
            title="Battle Training",
            description="Training session for warriors",
            creator=self.user,
            group=self.group,
            location=self.location,
            final_date=timezone.now() + datetime.timedelta(days=7),
            status=Event.ACTIVE,
            image="battle_training.jpg",
            is_private=False
        )

    def test_list_events(self):
        """
        Test listing events for groups the user is a member of.
        """
        url = reverse('list_of_events')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], "Battle Training")
        self.assertEqual(response.data[0]['creator'], self.user.id)

    def test_list_events_non_member(self):
        """
        Test listing events for a user not in any groups.
        """
        # Create a new user not in the group
        new_user = CustomUser.objects.create_user(
            username="Odin", email="Odin@asgard.com", password="allfather"
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(RefreshToken.for_user(new_user).access_token)}')
        url = reverse('list_of_events')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_create_event(self):
        """
        Test creating an event as a group creator.
        """
        url = reverse('list_of_events')
        data = {
            "title": "War Council",
            "description": "Strategic meeting",
            "creator": self.user.id,
            "group": self.group.id,
            "location": self.location.id,
            "image": "war_council.jpg",
            "is_private": False
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], "Event has been created successfully")
        self.assertTrue(Event.objects.filter(title="War Council").exists())
        event = Event.objects.get(title="War Council")
        self.assertEqual(event.creator, self.user)
        self.assertEqual(event.group, self.group)

    def test_create_event_non_admin(self):
        """
        Test creating an event as a non-admin/non-creator group member.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(RefreshToken.for_user(self.other_user).access_token)}')
        url = reverse('list_of_events')
        data = {
            "title": "Unauthorized Event",
            "description": "Should fail",
            "creator": self.other_user.id,
            "group": self.group.id,
            "location": self.location.id,
            "image": "unauthorized.jpg"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Creator must be an admin or creator", response.data['message'])
        self.assertFalse(Event.objects.filter(title="Unauthorized Event").exists())

    def test_create_event_unauthenticated(self):
        """
        Test creating an event without authentication.
        """
        self.client.credentials()
        url = reverse('list_of_events')
        data = {
            "title": "War Council",
            "description": "Strategic meeting",
            "creator": self.user.id,
            "group": self.group.id,
            "location": self.location.id,
            "image": "war_council.jpg"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_event_detail(self):
        """
        Test retrieving an event's details.
        """
        url = reverse('details_of_event', kwargs={'pk': self.event.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "Battle Training")
        self.assertEqual(response.data['creator'], self.user.id)
        self.assertEqual(response.data['group'], self.group.id)
        self.assertEqual(response.data['location'], self.location.id)

    def test_get_nonexistent_event(self):
        """
        Test retrieving a non-existent event.
        """
        url = reverse('details_of_event', kwargs={'pk': 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_event_full(self):
        """
        Test fully updating an event as the creator (PUT).
        """
        url = reverse('details_of_event', kwargs={'pk': self.event.id})
        data = {
            "title": "Updated Training",
            "description": "Updated session",
            "creator": self.user.id,
            "group": self.group.id,
            "location": self.location.id,
            "image": "updated_training.jpg",
            "is_private": True,
            "status": Event.ACTIVE
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "Updated Training")
        self.assertTrue(response.data['is_private'])
        self.event.refresh_from_db()
        self.assertEqual(self.event.title, "Updated Training")
        self.assertEqual(self.event.image, "updated_training.jpg")

    def test_update_event_partial(self):
        """
        Test partially updating an event (PATCH).
        """
        url = reverse('details_of_event', kwargs={'pk': self.event.id})
        data = {
            "title": "Patched Training",
            "is_private": True
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "Patched Training")
        self.assertTrue(response.data['is_private'])
        self.event.refresh_from_db()
        self.assertEqual(self.event.title, "Patched Training")

    def test_update_event_cancel(self):
        """
        Test updating an event to canceled status.
        """
        url = reverse('details_of_event', kwargs={'pk': self.event.id})
        data = {
            "title": "Battle Training",
            "description": "Training session for warriors",
            "creator": self.user.id,
            "group": self.group.id,
            "location": self.location.id,
            "image": "battle_training.jpg",
            "status": Event.CANCELED
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.event.refresh_from_db()
        self.assertEqual(self.event.status, Event.CANCELED)
        self.assertIsNotNone(self.event.canceled_at)

    def test_update_event_non_active(self):
        """
        Test updating a non-active event (should fail).
        """
        self.event.cancel()
        self.event.save()
        url = reverse('details_of_event', kwargs={'pk': self.event.id})
        data = {
            "title": "Invalid Update",
            "creator": self.user.id,
            "group": self.group.id,
            "location": self.location.id,
            "image": "invalid.jpg"
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Only active events can be updated", response.data['non_field_errors'][0])

    def test_update_event_non_creator(self):
        """
        Test updating an event as a non-creator/non-admin.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(RefreshToken.for_user(self.other_user).access_token)}')
        url = reverse('details_of_event', kwargs={'pk': self.event.id})
        data = {
            "title": "Forbidden Update",
            "creator": self.other_user.id,
            "group": self.group.id,
            "location": self.location.id,
            "image": "forbidden.jpg"
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_event(self):
        """
        Test deleting an event as the creator.
        """
        url = reverse('details_of_event', kwargs={'pk': self.event.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "Event deleted successfully")
        self.assertFalse(Event.objects.filter(id=self.event.id).exists())

    def test_delete_nonexistent_event(self):
        """
        Test deleting a non-existent event.
        """
        url = reverse('details_of_event', kwargs={'pk': 999})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['message'], "Event does not exist")

    def test_delete_event_non_creator(self):
        """
        Test deleting an event as a non-creator/non-admin.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(RefreshToken.for_user(self.other_user).access_token)}')
        url = reverse('details_of_event', kwargs={'pk': self.event.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)