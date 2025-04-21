from rest_framework import serializers
from django.core.exceptions import ValidationError
from api.models import Group, GroupMember, CustomUser

class GroupMemberSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), help_text="The user who is a member of the group")
    group = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all(), help_text="The group the user belongs to")
    role = serializers.ChoiceField(choices=GroupMember.ROLE_CHOICE, help_text="The role of the user in the group")
    joined_at = serializers.DateTimeField(read_only=True, help_text="When the user joined the group")

    class Meta:
        model = GroupMember
        fields = ['id', 'group', 'user', 'role', 'joined_at']
        read_only_fields = ['id', 'joined_at']

    def validate(self, data):
        """
        Ensure the user is not already a member of the group and validate role assignment.
        """
        group = data.get('group')
        user = data.get('user')
        role = data.get('role') 

        if self.instance is None:  
            if GroupMember.objects.filter(group=group, user=user).exists():
                raise serializers.ValidationError("User is already a member of this group")
        
        if role == GroupMember.CREATOR and (self.instance is None or self.instance.role != GroupMember.CREATOR):
            raise serializers.ValidationError("Creator role can only be assigned automatically to the group creator")
        
        return data

class GroupSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), help_text="The user who created the group")
    created_at = serializers.DateTimeField(read_only=True, help_text="When the group was created")
    members = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), many=True, help_text="List of user IDs who are members of the group")
    member_details = GroupMemberSerializer(source='groupmember_set', many=True, read_only=True, help_text="Details of group members including roles")

    class Meta:
        model = Group
        fields = ['id', 'name', 'description', 'created_by', 'created_at', 'is_private', 'members', 'member_details']
        read_only_fields = ['id', 'created_at', 'member_details']

    def validate_members(self, value):
        #Ensure the members list has a user
        if not value:
            raise serializers.ValidationError("Group must have at least one member (the creator)")
        #Ensure the creator the group is in the members list
        if self.initial_data.get('created_by') not in [user.id for user in value]:
            raise serializers.ValidationError("The creator must be included in the members list")
        return value

    def create(self, validated_data):
        """
        Create a new group and add members through GroupMember.
        """
        members = validated_data.pop('members', [])
        group = Group.objects.create(**validated_data)
        
        
        for member in members:
            if member != group.created_by:
                group.add_member(member)
        
        return group

    def update(self, instance, validated_data):
        """
        Update group details and sync members.
        """
        members = validated_data.pop('members', None)
        is_private = validated_data.get('is_private', None)

        # Handle privacy change
        if is_private is not None and is_private:
            instance.make_private()
            validated_data.pop('is_private', None)

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()

        # Sync members if provided
        if members is not None:
            current_members = set(instance.members.all())
            new_members = set(members)
            
            # Add new members
            for member in new_members - current_members:
                if member != instance.created_by:
                    instance.add_member(member)
            
            # Remove members
            for member in current_members - new_members:
                if member != instance.created_by:
                    instance.remove_member(member)
        
        return instance