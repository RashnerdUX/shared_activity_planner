from django.db import models, DatabaseError
from django.conf import settings
from django.core.exceptions import ValidationError

class Group(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="created_groups")
    created_at = models.DateTimeField(auto_now_add=True)
    is_private = models.BooleanField(default=False)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, through="GroupMember", related_name="member_groups")

    def __str__(self):
        description = (self.description[:50] + "...") if len(self.description) > 50 else self.description
        return f"{self.name} was created by {self.created_by} with the purpose - {description}"
    
    def make_private(self):
        if not self.is_private:
            self.is_private = True
            self.save()
            return True
        return False

    def save(self,**kwargs):
        # Check if this is a new group (no ID yet in the db)
        # my first save override
        is_new = self.pk is None
        super().save(**kwargs) #This saves the Group in the database
        # Automatically add creator as a GroupMember with CREATOR role
        try:
            GroupMember.objects.create(
                group=self,
                user=self.created_by,
                role=GroupMember.CREATOR
            )
        except Exception as e:
            raise DatabaseError(f"Failed to add creator as group member: {str(e)}")
    
    @staticmethod
    def has_group_role(user, group, roles):
        return GroupMember.objects.filter(
        group=group, user=user, role__in=roles,
        ).exists()
    
    def add_member(self, member):
        if member == self.created_by or self.members.filter(id=member.id).exists():
            raise ValidationError("Already a member of the group")
        GroupMember.objects.create(
            group = self,
            user = member,
            role = GroupMember.MEMBER,
        )
        return True
    
    def remove_member(self, member):
        if member == self.created_by:
            raise ValidationError("User can't remove himself as the creator of the group")
        if not self.members.filter(id=member.id).exists():
            raise ValidationError("Not a member of the group")
        GroupMember.objects.filter(group=self, user=member).delete()
        return True

class GroupMember(models.Model):
    ADMIN = "A"
    MEMBER = "M"
    CREATOR = "C"

    ROLE_CHOICE = [
        (ADMIN, "Administrator"),
        (MEMBER, "Member"),
        (CREATOR, "Creator"),
    ]

    group = models.ForeignKey(Group,on_delete=models.CASCADE, related_name="group_members")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="membership")
    role = models.CharField(max_length=1, choices=ROLE_CHOICE)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields = ["group_id", "user_id"],
                name = "unique_member_per_group"
            )
        ]

    def __str__(self):
        return f"{self.user} is a member of {self.group} and has {self.role} privileges"
    
    def change_role(self, new_role):
        if not new_role in [self.ADMIN, self.MEMBER, self.CREATOR]:
            raise ValidationError("The role being assigned to the user is invalid")
        if self.role == self.CREATOR:
            raise ValidationError("The creator role can not be changed")
        if self.role != new_role:
            self.role = new_role
            self.save()
            return True
        return False
    
