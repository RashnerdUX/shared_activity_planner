from datetime import datetime

from rest_framework import serializers
from django.utils import timezone

from api.models import Event, CustomUser, Group, Location
from .location_serializer import LocationSerializer

class EventSerializer(serializers.Serializer):
    """
    Gonna be testing PrimaryKeyRelated fields so take note when using in the views that all relationship fields are receiving an id for their respective objects when using the Event url
    """
    id = serializers.IntegerField(read_only = True)
    title = serializers.CharField()
    description = serializers.CharField(max_length=300, required=False,default="No description for this event")
    creator = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), help_text="Provide id of Creator of the event")
    group = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all(), help_text="Provide id for group associated with the Event")
    location = LocationSerializer(required=False)
    final_date = serializers.DateTimeField(read_only = True)
    status = serializers.CharField(max_length=1, default=Event.ACTIVE)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only = True)
    canceled_at = serializers.DateTimeField(read_only = True,allow_null=True)
    image = serializers.CharField(max_length=10000)
    is_private = serializers.BooleanField(default=False)

    def validate_final_date(self, value):
        if not isinstance(value, datetime.datetime):
            raise serializers.ValidationError("Final date must be a datetime.")
        return value

    def create(self, validated_data):
        if "is_private" not in validated_data:
            validated_data["is_private"] = validated_data["group"].is_private

        location_data = validated_data.pop('location', None)
        event = Event.objects.create(**validated_data)
        if location_data:
            print(location_data)
            event_location = Location.objects.create(**location_data)
            event.location = event_location
            event.save()
            validated_data["location"] = event_location
        return event
    
    def update(self, instance:Event, validated_data):
        if instance.status != Event.ACTIVE:
            raise serializers.ValidationError("Only active events can be updated")
        else:
            if "status" in validated_data:
                status = validated_data.pop("status")
                if status == Event.CANCELED:
                    instance.cancel()
                elif status == Event.COMPLETED:
                    instance.complete()

        if "is_private" in validated_data:
            if validated_data.get("is_private") and not instance.is_private:
                instance.make_private()
                validated_data.pop("is_private", None)
        
        if "location" in validated_data:
            location_data = validated_data.pop('location', None)
            if instance.location:
                for attr, value in location_data.items():
                    setattr(instance.location, attr, value)
                instance.location.save()
            else:
                location = Location.objects.create(**location_data)
                instance.location = location

        if "final_date" in validated_data:
            instance.set_final_date(validated_data.pop("final_date"))

        instance.title = validated_data.get("title", instance.title)
        instance.description = validated_data.get("description", instance.description)
        instance.image = validated_data.get("image", instance.image)
        instance.save()
        return instance

