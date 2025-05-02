from rest_framework import serializers

from api.models import Task, TaskCategory, Event, CustomUser, GroupMember

class TaskSerializer(serializers.ModelSerializer):

    assigned_to = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), required=False)
    
    class Meta:
        model = Task
        fields = ["id", "event", "category", "title", "description", "assigned_to", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_event(self, value):
        if not Event.objects.filter(pk=value.pk).exists():
            raise serializers.ValidationError("The event does not exist")
        return value
    
    def validate_category(self, value):
        if not TaskCategory.objects.filter(pk=value.pk).exists():
            raise serializers.ValidationError("The category hasn't been created yet")
        return value

    def validate(self, data):
        # Ensure event is provided for creation
        if self.instance is None and 'event' not in data:
            raise serializers.ValidationError("event is required")
        return data
    
    def update(self, instance, validated_data):
        if "status" in validated_data:
            status = validated_data.pop("status")
            if status == Task.ACTIVE:
                instance.accept_task()
            elif status == Task.COMPLETED: 
                instance.complete_task()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
    


class TaskCategorySerializer(serializers.ModelSerializer):
    
    class Meta:
        model = TaskCategory
        fields = ["id", "name", "description", "is_default", "created_by", "created_for"]
        read_only_fields = ["id"]

    def validate_name(self, value):
        if TaskCategory.objects.filter(name=value).exists():
            raise serializers.ValidationError(f"{value} already exists as a category in the database")
        return value
    
    def validate(self, validated_data):
        request = self.context.get("request")
        default_bool = validated_data.get("is_default")
        if not (request.user.is_staff or request.user.is_superuser) and default_bool:
            raise serializers.ValidationError("User is not an app admin so is unable to create a default task category")
        return validated_data