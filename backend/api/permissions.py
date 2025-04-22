from rest_framework import permissions, request

from .models import GroupMember, Event, Group

class CanManageGroupMembers(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        user = request.user
        try:
            member = obj.groupmember_set.get(user=user)
            return member.role in [GroupMember.ADMIN, GroupMember.CREATOR]
        except GroupMember.DoesNotExist:
            self.message = "User is not even a member of this group"
            return False
        
#Can edit an Event
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