import random
import datetime

from rest_framework.test import APITestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from api.models import Group, Event, Location, TimeOption, TimeVote
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.tokens import default_token_generator
from django.db.models import Count

CustomUser = get_user_model()


class TestTimeAndScheduling(APITestCase):

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
        self.location = Location.objects.create(
            name="Asgard Palace",
            address="1 Valhalla Road",
            city="Asgard",
            country="Asgard",
            latitude=0.0,
            longitude=0.0,
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

        self.time_option1 = TimeOption.objects.create(
            event = self.event,
            start_time = "2025-05-10T10:00:00Z",
            is_chosen = False
        )

    def test_create_time(self):
        url = reverse('event_scheduling', kwargs={"pk": self.event.id})
        data = {
            "event": self.event.id,
            "start_time": "2025-05-10T14:00:00Z",
            "end_time": "2025-05-10T16:00:00Z",
            "is_chosen": False
            }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_create_time_not_allowed(self):
        url = reverse('event_scheduling', kwargs={"pk": self.event.id})
        data = {
            "event": self.event.id,
            "start_time": "2025-05-10T15:00:00Z",
            "end_time": "2025-05-10T18:00:00Z",
            "is_chosen": False
            }
        
        refresh = RefreshToken.for_user(self.other_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_event_time_option(self):
        """
        Test retrieving a single time object
        """
        url = reverse('event_scheduling', kwargs={"pk": self.time_option1.id})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_get_event_time_options(self):
        """
        Test retrieving multiple time objects
        """
        TimeOption.objects.create(
            event = self.event,
            start_time = "2025-05-10T17:00:00Z",
            is_chosen = False
        )
        TimeOption.objects.create(
            event = self.event,
            start_time = "2025-05-10T20:00:00Z",
            is_chosen = False
        )
        url = reverse('list_of_event_time', query={"event":self.event.id})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_change_time_for_time_option(self):
        """
        This checks if the time option's start time can be edited. Endtime can only be edited for a time option that has been chosen
        """
        url = reverse('event_scheduling', kwargs={"pk": self.time_option1.id})
        data = {
            "start_time": "2025-05-10T20:00:00Z",
            "end_time": "2025-05-10T23:00:00Z"
        }

        response = self.client.patch(url, data)

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["end_time"])

    def test_delete_time_option(self):
        """
        This checks if the editors of an event can remove an event
        """
        url = reverse('event_scheduling', kwargs={"pk": self.time_option1.id})

        response = self.client.delete(url)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(TimeOption.objects.filter(pk=self.time_option1.id).exists())

    def test_delete_time_option_not_allowed(self):
        """
        This checks if a user that's not authorized to delete a time option is unable to
        """
        url = reverse('event_scheduling', kwargs={"pk": self.time_option1.id})

        refresh = RefreshToken.for_user(self.other_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)
        self.assertTrue(TimeOption.objects.filter(pk=self.time_option1.id).exists())

    def test_voting_ability(self):
        """
        This checks that users can vote on a time option
        """
        url = reverse('time_voting', kwargs={"pk": self.event.id})
        data = {
            "user":self.user.id,
            "time_option":self.time_option1.id
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 200)

    def test_voting_ability_any_role(self):
        """
        This makes sure all participants in an event can vote irrespective of role
        """
        url = reverse('time_voting', kwargs={"pk": self.event.id})
        data = {
            "user":self.user.id,
            "time_option":self.time_option1.id
        }
        refresh = RefreshToken.for_user(self.other_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 200)

    def test_voting_modification(self):
        """
        This checks if the user can modify their vote and ensures only their vote is modified
        """
        url_vote = reverse('time_voting', kwargs={"pk": self.event.id})

        #Create a vote
        data = {
            "user":self.user.id,
            "time_option":self.time_option1.id
        }
        response_vote = self.client.post(url_vote, data)
        #Create another time option
        self.time_option2 = TimeOption.objects.create(
            event = self.event,
            start_time = "2025-05-10T20:00:00Z",
            is_chosen = False
        )
        #Modify the vote after creating it
        vote = TimeVote.objects.filter(user=self.user, time_option__event=self.event).first()
        if vote:
            vote_id = vote.id
        else:
            vote_id = None
            raise Exception("Vote does not exist")
        
        url_modify = reverse('modify_time_vote', kwargs={"pk": vote.id})
        data_modify_vote = {
            "time_option":self.time_option2.id
        }
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.accesstoken}')
        response = self.client.patch(url_modify, data_modify_vote)
        self.assertEqual(response.status_code, 200)
    
    def test_count_votes(self):
        url = reverse('time_vote_count', kwargs={"pk": self.event.id})

        self.time_option2 = TimeOption.objects.create(
            event = self.event,
            start_time = "2025-05-10T20:00:00Z",
            is_chosen = False
        )
        self.time_option3 = TimeOption.objects.create(
            event = self.event,
            start_time = "2025-05-10T21:00:00Z",
            is_chosen = False
        )

        for t in TimeOption.objects.filter(event=self.event):
            rand_votes = random.randint(10,200)
            for n in range(rand_votes):
                user = CustomUser.objects.create_user(username=f"testuser_{t.id}_{n}", email=f"testuser{t.id}_{n}@example.com")
                TimeVote.objects.create(user=user, time_option=t)

        for t in TimeOption.objects.filter(event=self.event):
            t.refresh_from_db()
        
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        for time_option in response.data:
            self.assertIn('no_of_votes', time_option)
            self.assertIsNotNone(time_option['no_of_votes'])
            self.assertIsInstance(time_option['no_of_votes'], int)
            self.assertGreaterEqual(time_option['no_of_votes'], 10)


    def test_schedule_event_final_date(self):
        """
        This tests that after votes have been carried out and concluded. The final date set is the one with the highest votes and if there's a tie, the defacto vote is the first one
        """
        url = reverse('set_final_time', kwargs={"pk": self.event.id})

        self.time_option2 = TimeOption.objects.create(
            event = self.event,
            start_time = "2025-05-10T20:00:00Z",
            is_chosen = False
        )
        self.time_option3 = TimeOption.objects.create(
            event = self.event,
            start_time = "2025-05-10T21:00:00Z",
            is_chosen = False
        )

        #Artificially create votes for an event
        for t in TimeOption.objects.filter(event=self.event):
            rand_votes = random.randint(10,200)
            for n in range(rand_votes):
                user = CustomUser.objects.create_user(username=f"testuser_{t.id}_{n}", email=f"testuser{t.id}_{n}@example.com")
                TimeVote.objects.create(user=user, time_option=t)

        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 200)
        #This ensures that the time with highest vote and the time chosen for the event are the same
        voted_time_option = TimeOption.objects.filter(event=self.event)\
            .annotate(actual_votes=Count("votes"))\
                .order_by('-actual_votes', "pk")\
                    .first()\
                        .start_time
        self.assertIn(str(voted_time_option), response.data["message"])


            

        
