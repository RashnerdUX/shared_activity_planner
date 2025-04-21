from rest_framework import permissions, request

from .models import GroupMember, Events

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

    def has_object_permission(self, request, view, obj:Events):
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
            group = obj,
            user = user,
            role__in = [GroupMember.ADMIN, GroupMember.CREATOR],
        ).exists:
            return True
        
        self.message = "User can not edit the event because User isn't a creator or admin associated with the event"
        return False
            