import logging

from rest_framework import permissions, request
from django.shortcuts import get_object_or_404

from .models import GroupMember, Event, Group, Participant, TimeVote

logger = logging.getLogger(__name__)

class CanManageGroupMembers(permissions.BasePermission):
    """
    This ensures that only admin and creators of the group can manage group membership
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        try:
            member = obj.group_members.get(user=user)
            return member.role in [GroupMember.ADMIN, GroupMember.CREATOR]
        except GroupMember.DoesNotExist:
            self.message = "User is not even a member of this group"
            return False
        
class CanEditEventDetails(permissions.BasePermission):
    message = "User is not the creator of the event"

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj:Event):
        user = request.user
        
        #This protects who can see an Event
        if request.method == permissions.SAFE_METHODS:
            if obj.is_private:
                if not (obj.is_private or obj.group.is_private):
                    return True
                if GroupMember.objects.filter(group=obj.group, user=user).exists():
                    return True
                self.message = "User is not allowed to view this event. It is private"
                return False
        
        #This ensures only the creator can edit an event
        if obj.creator == user:
            return True
        #This allows group members that are admin or the group creator to edit an event
        if GroupMember.objects.filter(
            group = obj.group,
            user = user,
            role__in = [GroupMember.ADMIN, GroupMember.CREATOR],
        ).exists():
            return True
        
        self.message = "User can not edit the event because User isn't a creator or admin associated with the event"
        return False
            
class CanCreateAnEventForGroup(permissions.BasePermission):
    """
    This permission allows admins and creator of a group the ability to create an event for that group
    """

    def has_permission(self, request, view):
        user = request.user
        #Get the members for the group

        group_id = request.data.get("group")

        if request.method == permissions.SAFE_METHODS:
            return True
        
        if not group_id:
            self.message = "Group ID is required to create an event"
            return False

        try:
            group = Group.objects.get(pk=group_id)

            group_member = GroupMember.objects.filter(group=group, user=user).first()
            if group_member.role == GroupMember.ADMIN or group_member.role == GroupMember.CREATOR:
                return True
            else:
                self.message = "User is not allowed to create an event in this group"
                return False
        except Group.DoesNotExist:
            self.message = "The group does not exist"
            return False
        
class CanVoteOnEventAndModifyVote(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user

        if request.method == "PATCH":
            vote_id = view.kwargs.get("pk")
            try:
                vote = TimeVote.objects.get(pk=vote_id)
                return vote.user == user
            except TimeVote.DoesNotExist:
                return False

        elif request.method == "POST":
            event_id = view.kwargs.get("pk")  # depends on URL pattern
            try:
                event = Event.objects.get(pk=event_id)
                is_participant = Participant.objects.filter(event=event, user=user).exists()
                is_member = event.group and GroupMember.objects.filter(group=event.group, user=user).exists()
                return is_participant or is_member
            except Event.DoesNotExist:
                return False

        return False
        
class CanCreateATimeOption(permissions.BasePermission):

    def has_permission(self, request, view):
        user = request.user
        #Get the members for the event
        event = request.data.get("event")

        if not event:
            self.message = "No event id was passed in the request"
            return False

        if request.method == permissions.SAFE_METHODS:
            return True
        
        try:
            event = Event.objects.get(pk=event)
            try:
                membership = GroupMember.objects.get(user=user, group=event.group)
                if membership.role in [GroupMember.CREATOR, GroupMember.ADMIN]:
                    return True
                else:
                    self.message = "User is neither an admin or creator so can't add a time option for voting"
                    return False
            except GroupMember.DoesNotExist:
                self.message = "User is not a member of the group"
                return False
        except Event.DoesNotExist:
            self.message = "The event id passed does not link to any event"
            return False
        except Exception as e:
            self.message = f"{e}"
            return False

class CanCreateTaskForEvent(permissions.BasePermission):
    """
    Allows access to TaskListView only for the event creator or group members of the event's group.
    Checks event from query_params (GET) or data (POST).
    """
    def has_permission(self, request, view):
        # Extract event based on request method
        if request.method == 'GET':
            event = request.query_params.get('event')
        else:  # POST
            event = request.data.get('event')

        #Approve permission if event does not exist without checking the user's permission
        if not Event.objects.filter(pk=event).exists():
            self.message = "The Event does not exist"
            return True
        
        if not event:
            return False  # Deny if event is missing
        
        try:
            event = Event.objects.get(pk=event)
            # Allow if user is the event creator
            if request.user == event.creator:
                return True
            # Allow if user is a group member
            if event.group and GroupMember.objects.filter(group=event.group, user=request.user).exists():
                return True
            return False
        except Event.DoesNotExist:
            return False  # Deny if event doesn't exist
        
class CanAccessOrModifyTask(permissions.BasePermission):
    """
    Allows access to TaskView.get and TaskView.patch for:
    - Event creator
    - Group members (GET) or group admins/creators (PATCH)
    - User assigned to the task (GET and PATCH)
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        event = obj.event
        # Allow if user is the event creator
        if user == event.creator:
            return True

        # Allow if user is the assigned user
        if user == obj.assigned_to:
            return True

        # Check group membership
        if event.group:
            try:
                member = GroupMember.objects.get(group=event.group, user=user)
                # For GET, allow any group member
                if request.method in permissions.SAFE_METHODS:
                    return True
                # For PATCH, allow only admins or creators
                return member.role in [GroupMember.ADMIN, GroupMember.CREATOR]
            except GroupMember.DoesNotExist:
                return False     
        return False
    
class IsAdminOrStaffForDefaultCategory(permissions.BasePermission):
    """
    Allows only admin (is_superuser) or staff (is_staff) to edit default task categories.
    All authenticated users can retrieve categories.
    """
    def has_object_permission(self, request, view, obj):
        # Allow GET for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        # Allow PATCH/DELETE only for admin/staff if is_default=True
        if obj.is_default:
            return request.user.is_superuser or request.user.is_staff
        # Allow PATCH/DELETE for non-default categories to authenticated users
        return True

class CanChangeTaskStatus(permissions.BasePermission):
    """
    Allows event creators, group admins/creators, or the assigned user to change task status.
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        event = obj.event
        # Allow if user is the event creator
        if user == event.creator:
            return True
        # Allow if user is the assigned user
        if user == obj.assigned_to:
            return True
        # Check if user is a group admin or creator
        if event.group:
            try:
                member = GroupMember.objects.get(group=event.group, user=user)
                return member.role in [GroupMember.ADMIN, GroupMember.CREATOR]
            except GroupMember.DoesNotExist:
                return False
        return False

class CanAssignTask(permissions.BasePermission):
    """
    Allows only event creators or group admins/creators to assign tasks.
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        event = obj.event
        # Allow if user is the event creator
        if user == event.creator:
            return True
        # Check if user is a group admin or creator
        if event.group:
            try:
                member = GroupMember.objects.get(group=event.group, user=user)
                return member.role in [GroupMember.ADMIN, GroupMember.CREATOR]
            except GroupMember.DoesNotExist:
                return False
        return False