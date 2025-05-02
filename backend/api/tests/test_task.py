from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.tokens import default_token_generator
from api.models import Task, TaskCategory, Event, Group, Location
import datetime

CustomUser = get_user_model()

class TaskAndTaskCategoryTests(APITestCase):
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
        
        # Create an admin user
        self.admin_user = CustomUser.objects.create_superuser(
            username="Odin",
            email="Odin@asgard.com",
            password="allfather123"
        )
        refresh_admin = RefreshToken.for_user(self.admin_user)
        self.admin_accesstoken = str(refresh_admin.access_token)
        
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
        
        # Create a non-default task category
        self.category = TaskCategory.objects.create(
            name="Training",
            description="Tasks for training sessions",
            is_default=False,
            created_by=self.user,
            created_for=self.event
        )
        
        # Create a default task category
        self.default_category = TaskCategory.objects.create(
            name="Default",
            description="Default category",
            is_default=True,
            created_by=self.admin_user,
            created_for=self.event
        )
        
        # Create a test task
        self.task = Task.objects.create(
            event=self.event,
            category=self.category,
            title="Sword Practice",
            description="Practice sword fighting",
            assigned_to=self.other_user,
            status=Task.PENDING
        )

    # TaskListView Tests
    def test_list_tasks_event_creator(self):
        url = reverse('task_list') + f'?event={self.event.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], "Sword Practice")

    def test_list_tasks_group_member(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(self.other_user).access_token}')
        url = reverse('task_list') + f'?event={self.event.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_tasks_non_member(self):
        non_member = CustomUser.objects.create_user(username="Sif", email="Sif@asgard.com", password="warrior123")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(non_member).access_token}')
        url = reverse('task_list') + f'?event={self.event.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_tasks_invalid_event(self):
        url = reverse('task_list') + '?event=999'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['message'], "Event with ID 999 does not exist")

    def test_create_task_event_creator(self):
        url = reverse('task_list')
        data = {
            "event": self.event.id,
            "category": self.category.id,
            "title": "Shield Training",
            "description": "Practice with shields",
            "status": Task.PENDING
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], "Shield Training")
        self.assertEqual(Task.objects.count(), 2)

    def test_create_task_group_member_non_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(self.other_user).access_token}')
        url = reverse('task_list')
        data = {
            "event": self.event.id,
            "category": self.category.id,
            "title": "Shield Training",
            "description": "Practice with shields",
            "status": Task.PENDING
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['error'], f"Was unable to create a task for {self.event.title}")

    def test_create_task_invalid_event(self):
        url = reverse('task_list')
        data = {
            "event": 999,
            "category": self.category.id,
            "title": "Shield Training",
            "description": "Practice with shields",
            "status": Task.PENDING
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # TaskView Tests
    def test_retrieve_task_event_creator(self):
        url = reverse('task_detail', kwargs={'pk': self.task.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "Sword Practice")

    def test_retrieve_task_assignee(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(self.other_user).access_token}')
        url = reverse('task_detail', kwargs={'pk': self.task.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "Sword Practice")

    def test_retrieve_task_non_authorized(self):
        non_member = CustomUser.objects.create_user(username="Sif", email="Sif@asgard.com", password="warrior123")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(non_member).access_token}')
        url = reverse('task_detail', kwargs={'pk': self.task.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_task_event_creator(self):
        url = reverse('task_detail', kwargs={'pk': self.task.id})
        data = {"title": "Advanced Sword Practice"}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, "Advanced Sword Practice")

    def test_update_task_assignee(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(self.other_user).access_token}')
        url = reverse('task_detail', kwargs={'pk': self.task.id})
        data = {"description": "Updated description"}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.description, "Updated description")

    def test_update_task_non_authorized(self):
        non_member = CustomUser.objects.create_user(username="Sif", email="Sif@asgard.com", password="warrior123")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(non_member).access_token}')
        url = reverse('task_detail', kwargs={'pk': self.task.id})
        data = {"title": "Unauthorized Update"}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_task_event_creator(self):
        url = reverse('task_detail', kwargs={'pk': self.task.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        with self.assertRaises(ObjectDoesNotExist):
            Task.objects.get(pk=self.task.id)

    def test_delete_task_non_authorized(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(self.other_user).access_token}')
        url = reverse('task_detail', kwargs={'pk': self.task.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Task.objects.filter(pk=self.task.id).exists())

    # TaskAssignmentView Tests
    def test_assign_task_event_creator(self):
        url = reverse('task_assign', kwargs={'pk': self.task.id})
        data = {"assigned_to": self.user.id}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.assigned_to, self.user)

    def test_assign_task_non_authorized(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(self.other_user).access_token}')
        url = reverse('task_assign', kwargs={'pk': self.task.id})
        data = {"assigned_to": self.user.id}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.task.refresh_from_db()
        self.assertEqual(self.task.assigned_to, self.other_user)

    # ChangeTaskStatusView Tests
    def test_change_task_status_event_creator(self):
        url = reverse('task_status', kwargs={'pk': self.task.id})
        data = {"status": Task.ACTIVE}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.ACTIVE)

    def test_change_task_status_assignee(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(self.other_user).access_token}')
        url = reverse('task_status', kwargs={'pk': self.task.id})
        data = {"status": Task.COMPLETED}

        #Make the event active
        self.task.status = Task.ACTIVE
        self.task.save()

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.COMPLETED)

    def test_change_task_status_non_authorized(self):
        non_member = CustomUser.objects.create_user(username="Sif", email="Sif@asgard.com", password="warrior123")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(non_member).access_token}')
        url = reverse('task_status', kwargs={'pk': self.task.id})
        data = {"status": Task.ACTIVE}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # TaskCategoryListView Tests
    def test_list_task_categories(self):
        url = reverse('task_category_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 12)
        self.assertEqual(response.data[0]['name'], "Activities")  # Ordered by name

    def test_create_task_category_regular_user(self):
        url = reverse('task_category_list')
        data = {
            "name": "Logistics & Transport F",
            "description": "Tasks for event logistics",
            "is_default": False,
            "created_by": self.user.id,
            "created_for": self.event.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], "Logistics & Transport F")
        self.assertEqual(TaskCategory.objects.count(), 13)

    def test_create_default_task_category_non_admin(self):
        url = reverse('task_category_list')
        data = {
            "name": "Emergency",
            "description": "Emergency tasks",
            "is_default": True,
            "created_by": self.user.id,
            "created_for": self.event.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("User is not an app admin", str(response.data))

    def test_create_default_task_category_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_accesstoken}')
        url = reverse('task_category_list')
        data = {
            "name": "Emergency",
            "description": "Emergency tasks",
            "is_default": True,
            "created_by": self.admin_user.id,
            "created_for": self.event.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], "Emergency")

    # TaskCategoryView Tests
    def test_retrieve_task_category(self):
        url = reverse('task_category_detail', kwargs={'pk': self.category.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Training")

    def test_update_default_task_category_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_accesstoken}')
        url = reverse('task_category_detail', kwargs={'pk': self.default_category.id})
        data = {"description": "Updated default category"}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.default_category.refresh_from_db()
        self.assertEqual(self.default_category.description, "Updated default category")

    def test_update_default_task_category_non_admin(self):
        url = reverse('task_category_detail', kwargs={'pk': self.default_category.id})
        data = {"description": "Unauthorized update"}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_default_task_category_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_accesstoken}')
        url = reverse('task_category_detail', kwargs={'pk': self.default_category.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        with self.assertRaises(ObjectDoesNotExist):
            TaskCategory.objects.get(pk=self.default_category.id)

    def test_delete_default_task_category_non_admin(self):
        url = reverse('task_category_detail', kwargs={'pk': self.default_category.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(TaskCategory.objects.filter(pk=self.default_category.id).exists())