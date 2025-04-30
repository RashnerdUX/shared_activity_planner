from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from api.models import Group, GroupMember
from api.serializers import GroupSerializer, GroupMemberSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.tokens import default_token_generator

CustomUser = get_user_model()

class GroupViewsTests(APITestCase):
    def setUp(self):
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
        
        # Create another user for testing
        self.other_user = CustomUser.objects.create_user(
            username="Loki",
            email="Loki@asgard.com",
            password="trickster123",
            first_name="Loki",
            last_name="Laufeyson"
        )
        
        # Create a test group
        self.group = Group.objects.create(
            name="Asgard Warriors",
            description="A group for Asgard's finest warriors",
            created_by=self.user,
            is_private=False
        )
        # Creator is automatically added as a member with CREATOR role via Group.save()

    def test_list_groups(self):
        """
        Test listing all groups.
        """
        url = reverse('group_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "Asgard Warriors")

    def test_list_my_groups(self):
        """
        Test listing groups where the user is a member.
        """
        url = reverse('group_list') + '?my_groups=true'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "Asgard Warriors")
        
        # Test with a user who is not a member
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(RefreshToken.for_user(self.other_user).access_token)}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_create_group(self):
        """
        Test creating a new group.
        """
        url = reverse('group_list')
        data = {
            "name": "Valhalla Heroes",
            "description": "A group for Valhalla's champions",
            "members": [self.user.id, self.other_user.id],
            "is_private": False
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], "Valhalla Heroes")
        self.assertEqual(response.data['created_by'], self.user.id)
        self.assertIn(self.other_user.id, response.data['members'])
        self.assertEqual(
            GroupMember.objects.get(group__name="Valhalla Heroes", user=self.user).role,
            GroupMember.CREATOR
        )

    def test_create_group_unauthenticated(self):
        """
        Test creating a group without authentication.
        """
        self.client.credentials()  # Remove authentication
        url = reverse('group_list')
        data = {
            "name": "Valhalla Heroes",
            "description": "A group for Valhalla's champions",
            "members": [self.user.id]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_group_detail(self):
        """
        Test retrieving a group's details.
        """
        url = reverse('group_details', kwargs={'pk': self.group.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Asgard Warriors")
        self.assertEqual(len(response.data['member_details']), 1)
        self.assertEqual(response.data['member_details'][0]['role'], GroupMember.CREATOR)

    def test_update_group(self):
        """
        Test updating a group as the creator.
        """
        url = reverse('group_details', kwargs={'pk': self.group.id})
        data = {
            "name": "Updated Warriors",
            "description": "Updated description",
            "is_private": True
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Updated Warriors")
        self.assertTrue(response.data['is_private'])

    def test_update_group_non_creator(self):
        """
        Test updating a group as a non-creator.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(RefreshToken.for_user(self.other_user).access_token)}')
        url = reverse('group_details', kwargs={'pk': self.group.id})
        data = {"name": "Forbidden Update"}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_group(self):
        """
        Test deleting a group as the creator.
        """
        url = reverse('group_details', kwargs={'pk': self.group.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Group.objects.filter(id=self.group.id).exists())

    def test_delete_group_non_creator(self):
        """
        Test deleting a group as a non-creator.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(RefreshToken.for_user(self.other_user).access_token)}')
        url = reverse('group_details', kwargs={'pk': self.group.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_group_members(self):
        """
        Test listing all members of a group.
        """
        url = reverse('group_members', kwargs={'pk': self.group.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['user'], self.user.id)
        self.assertEqual(response.data[0]['role'], GroupMember.CREATOR)

    def test_add_group_member(self):
        """
        Test adding a new member as the creator.
        """
        url = reverse('group_members', kwargs={'pk': self.group.id})
        data = {"user_id": self.other_user.id}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user'], self.other_user.id)
        self.assertEqual(response.data['role'], GroupMember.MEMBER)
        self.assertTrue(GroupMember.objects.filter(group=self.group, user=self.other_user).exists())

    def test_add_group_member_non_creator(self):
        """
        Test adding a member as a non-creator/non-admin.
        """
        # Add other_user as a regular member
        self.group.add_member(self.other_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(RefreshToken.for_user(self.other_user).access_token)}')
        url = reverse('group_members', kwargs={'pk': self.group.id})
        data = {"user_id": CustomUser.objects.create_user(username="Odin", email="Odin@asgard.com", password="allfather").id}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_add_existing_member(self):
        """
        Test adding a user who is already a member.
        """
        url = reverse('group_members', kwargs={'pk': self.group.id})
        data = {"user_id": self.user.id}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Already a member", response.data['detail'])

    def test_remove_group_member(self):
        """
        Test removing a member as the creator.
        """
        self.group.add_member(self.other_user)
        url = reverse('group_members', kwargs={'pk': self.group.id})
        data = {"user_id": self.other_user.id}
        response = self.client.delete(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(GroupMember.objects.filter(group=self.group, user=self.other_user).exists())

    def test_remove_creator(self):
        """
        Test attempting to remove the creator.
        """
        url = reverse('group_members', kwargs={'pk': self.group.id})
        data = {"user_id": self.user.id}
        response = self.client.delete(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("can't remove himself", response.data['detail'])

    def test_remove_non_member(self):
        """
        Test removing a user who is not a member.
        """
        url = reverse('group_members', kwargs={'pk': self.group.id})
        data = {"user_id": self.other_user.id}
        response = self.client.delete(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Not a member", response.data['detail'])

    def test_change_member_role(self):
        """
        Test changing a member's role as the creator.
        """
        self.group.add_member(self.other_user)
        url = reverse('group_members', kwargs={'pk': self.group.id})
        data = {"user_id": self.other_user.id, "role": GroupMember.ADMIN}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['role'], GroupMember.ADMIN)
        self.assertEqual(
            GroupMember.objects.get(group=self.group, user=self.other_user).role,
            GroupMember.ADMIN
        )

    def test_change_creator_role(self):
        """
        Test attempting to change the creator's role.
        """
        url = reverse('group_members', kwargs={'pk': self.group.id})
        data = {"user_id": self.user.id, "role": GroupMember.MEMBER}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("creator role can not be changed", response.data['detail'])

    def test_change_role_non_creator(self):
        """
        Test changing a role as a non-creator/non-admin.
        """
        self.group.add_member(self.other_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(RefreshToken.for_user(self.other_user).access_token)}')
        url = reverse('group_members', kwargs={'pk': self.group.id})
        data = {"user_id": self.other_user.id, "role": GroupMember.ADMIN}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_change_role_invalid(self):
        """
        Test changing a role to an invalid value.
        """
        self.group.add_member(self.other_user)
        url = reverse('group_members', kwargs={'pk': self.group.id})
        data = {"user_id": self.other_user.id, "role": "INVALID"}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("invalid", response.data['detail'])

    def test_change_role_non_member(self):
        """
        Test changing the role of a non-member.
        """
        url = reverse('group_members', kwargs={'pk': self.group.id})
        data = {"user_id": self.other_user.id, "role": GroupMember.ADMIN}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)