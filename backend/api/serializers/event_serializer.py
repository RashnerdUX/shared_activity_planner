from rest_framework import serializers
from datetime import datetime

from api.models import Event, CustomUser, Group, Location

class EventSerializer(serializers.Serializer):
    """
    Gonna be testing PrimaryKeyRelated fields so take note when using in the views that all relationship fields are receiving an id for their respective objects when using the Event url
    """
    id = serializers.IntegerField(read_only = True)
    title = serializers.CharField()
    description = serializers.CharField(max_length=300, required=False,default="No description for this event")
    creator = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), help_text="Provide id of Creator of the event")
    group = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all(), help_text="Provide id for group associated with the Event")
    location = serializers.PrimaryKeyRelatedField(queryset=Location.objects.all(), help_text="Provide id for the location of the event")
    final_date = serializers.DateTimeField(read_only = True)
    status = serializers.CharField(max_length=1, required=True, default=Event.ACTIVE)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only = True)
    canceled_at = serializers.DateTimeField(read_only = True, blank=True, null=True)
    image = serializers.CharField(max_length=10000)
    is_private = serializers.BooleanField(default=False)

    def validate_final_date(self, value):
        if not isinstance(value, datetime.datetime):
            raise serializers.ValidationError("Final date must be a datetime.")
        return value

    def create(self, validated_data):
        if "is_private" not in validated_data:
            validated_data["is_private"] = validated_data["group"].is_private
        return Event.objects.create(**validated_data)
    
    def update(self, instance:Event, validated_data):
        if instance.status != Event.ACTIVE:
            raise serializers.ValidationError("Only active events can be updated")
        else:
            if "status" in validated_data:
                status = validated_data.pop("status") #Remove the value of status from validated data and apply the model methods to update it
                if status == Event.CANCELED:
                    instance.cancel()
                    instance.canceled_at = datetime.now()
                elif status == Event.COMPLETED:
                    instance.complete()

        if "is_private" in validated_data:
            if validated_data.get("is_private") and not instance.is_private:
                instance.make_private()
                validated_data.pop("is_private", None)
        
        if "location" in validated_data:
            instance.set_location(validated_data.pop("location"))

        if "final_date" in validated_data:
            instance.set_final_date(validated_data.pop("final_date"))

        instance.title = validated_data.get("title", instance.title)
        instance.description = validated_data.get("description", instance.description)
        instance.image = validated_data.get("image", instance.image)
        instance.save()
        return instance

