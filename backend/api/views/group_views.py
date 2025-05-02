from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.conf import settings

from api.models import Group, GroupMember, CustomUser
from api.serializers import GroupSerializer, GroupMemberSerializer
from api.permissions import CanManageGroupMembers


class GroupListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        List all groups or filter by user membership if 'my_groups' query param is provided.
        """
        my_groups = request.query_params.get('my_groups', None)
        if my_groups:
            groups = Group.objects.filter(members=request.user)
        else:
            groups = Group.objects.all()
        
        serializer = GroupSerializer(groups, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Create a new group with the authenticated user as the creator.
        """
        serializer = GroupSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GroupDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(Group, pk=pk)

    def get(self, request, pk):
        """
        Retrieve details of a specific group.
        """
        group = self.get_object(pk)
        serializer = GroupSerializer(group)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        """
        Update a group's details. Only the creator can update.
        """
        group = self.get_object(pk)
        if group.created_by != request.user:
            return Response(
                {"detail": "Only the creator can update this group"},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = GroupSerializer(group, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """
        Delete a group. Only the creator can delete.
        """
        group = self.get_object(pk)
        if group.created_by != request.user:
            return Response(
                {"detail": "Only the creator can delete this group"},
                status=status.HTTP_403_FORBIDDEN
            )
        group.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class GroupMembersView(APIView):
    permission_classes = [IsAuthenticated, CanManageGroupMembers]

    def get_object(self, pk):
        """
        Helper method to retrieve a group or return 404.
        """
        return get_object_or_404(Group, pk=pk)

    def get(self, request, pk):
        """
        List all members of a specific group.
        """
        group = self.get_object(pk)
        self.check_object_permissions(request, group)
        members = group.group_members.all()
        serializer = GroupMemberSerializer(members, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, pk):
        """
        Add a new member to the group. Only the creator or admins can add members.
        """
        group = self.get_object(pk)
        self.check_object_permissions(request, group)
        
        user_id = request.data.get('user_id')
        if not user_id:
            return Response(
                {"detail": "user_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = get_object_or_404(CustomUser, pk=user_id)
            group.add_member(user)
            member = GroupMember.objects.get(group=group, user=user)
            serializer = GroupMemberSerializer(member)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """
        Remove a member from the group. Only the creator or admins can remove members.
        """
        group = self.get_object(pk)
        self.check_object_permissions(request, group)
        
        user_id = request.data.get('user_id')
        if not user_id:
            return Response(
                {"detail": "user_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = get_object_or_404(CustomUser, pk=user_id)
            group.remove_member(user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        """
        Change a member's role in the group. Only the creator or admins can change roles.
        """
        group = self.get_object(pk)
        self.check_object_permissions(request, group)
        
        user_id = request.data.get('user_id')
        new_role = request.data.get('role')
        
        if not user_id or not new_role:
            return Response(
                {"detail": "Both user_id and role are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            member = get_object_or_404(GroupMember, group=group, user__id=user_id)
            member.change_role(new_role)
            serializer = GroupMemberSerializer(member)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except GroupMember.DoesNotExist:
            return Response(
                {"detail": "User is not a member of this group"},
                status=status.HTTP_404_NOT_FOUND
            )