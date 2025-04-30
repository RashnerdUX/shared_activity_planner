from datetime import datetime
from django.utils import timezone
from rest_framework import serializers

from api.models import TimeOption, TimeVote, Participant, Event, GroupMember
from api.serializers import EventSerializer

class TimeOptionSerializer(serializers.ModelSerializer):
    end_time = serializers.DateTimeField(allow_null = True, required=False)
    event_name = serializers.CharField(source="event.title", read_only=True)
    no_of_votes = serializers.IntegerField(read_only=True)

    class Meta:
        model = TimeOption
        fields = ["id", "event", "event_name", "start_time", "end_time","no_of_votes", "is_chosen"]
        read_only_fields = ["id", "event_name", "no_of_votes"]

    def validate_start_time(self, value):
        if not value:
            raise serializers.ValidationError(f"Start time must be added")
        if value <= timezone.now():
            raise serializers.ValidationError(f"Start time must be set in the future, ahead of {datetime.now}")
        return value

    def validate(self, data):

        event = data.get("event", getattr(self.instance, "event", None))

        if event.status != Event.ACTIVE:
            raise serializers.ValidationError("Cannot create a time option for an inactive event")
        
        start_time = data.get("start_time", self.instance.start_time if self.instance else None)
        end_time = data.get("end_time")
        if end_time and start_time and end_time <= start_time:
            raise serializers.ValidationError("End time must be after start time")
        
        return data
    
    def update(self, instance:TimeOption, validated_data):
        """
        Update the is_chosen bool and endtime if they are provided in the data sent by the client 
        """
        if "is_chosen" in validated_data:
            is_chosen = validated_data.pop("is_chosen")
            if is_chosen:
                instance.set_chosen_time()
        
        if "end_time" in validated_data:
            end_time = validated_data.pop("end_time")
            instance.set_end_time(closing_time=end_time)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance

class TimeVoteSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only = True)

    class Meta:
        model = TimeVote
        fields = ["id", "user", "username", "time_option", "voted_at"]
        read_only_fields = ["id", "username","voted_at"]

    def validate(self, data):
        time_option = data.get("time_option")
        event = self.context.get("event")
        request = self.context.get("request")
        user = request.user

        if event.status != Event.ACTIVE:
            raise serializers.ValidationError("Cannot vote for an inactive event")

        if not time_option:
            raise serializers.ValidationError("Client needs to provide a time option to vote")
        
        if not event:
            raise serializers.ValidationError("Needs event object to properly validate the TimeVote")
        
        #This ensures that non attendees don't influence the election
        is_member = GroupMember.objects.filter(user=user, group=event.group).exists()
        is_participant = Participant.objects.filter(event=event, user=user).exists()

        #Make sure the user casting a vote is attending
        if not (is_member or is_participant) :
            raise serializers.ValidationError("User is not attending this event so is unable to vote")
        

        if TimeVote.objects.filter(user=user, time_option__event=event, time_option=time_option).exists():
            raise serializers.ValidationError("You have already cast a vote for this event  for this time option.")

        #if TimeVote.objects.filter(user=user, time_option__event=event).exists():
            #raise serializers.ValidationError("You have already cast a vote for this event.")
        
        #Ensure the time option is one associated with the event
        if time_option.event != event:
            raise serializers.ValidationError("The time option isn't associated with the event")

        return data
    
    def update(self, instance: TimeVote, validated_data):
        new_time_option = validated_data.get("time_option")
        if new_time_option and instance.change_vote(new_time_option):
            return instance
        raise serializers.ValidationError(f"The time vote was not updated because {new_time_option} is not valid")
        

