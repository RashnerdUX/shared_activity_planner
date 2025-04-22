from rest_framework import serializers

from api.models import Event, CustomUser, Participant

class ParticipantSerializer(serializers.ModelSerializer):
    event = serializers.PrimaryKeyRelatedField(queryset=Event.objects.all(), help_text="Events that the user can attend")
    user = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), help_text="The user invited to these events")
    rsvp_status = serializers.ChoiceField(choices=Participant.RSVP_CHOICES, help_text="RSVP status of the participant")
    joined_at = serializers.DateTimeField(read_only=True, help_text="When the user was added to an event")
    username = serializers.CharField(source='user.username', read_only=True, help_text="Username of the participant")

    class Meta:
        model = Participant
        fields = ["id","event", "user","username","rsvp_status", "joined_at"]
        read_only_fields = ["id", "joined_at", "username"]

    def validate(self, data):
        event = data.get('event')
        user = data.get('user')
        
        if event.status != Event.ACTIVE:
            raise serializers.ValidationError("Cannot RSVP to a non-active event.")
       
        if event.is_private and not event.group.members.filter(id=user.id).exists():
            raise serializers.ValidationError("User must be a member of the event's group.")
        
        if self.instance is None and Participant.objects.filter(event=event, user=user).exists():
            raise serializers.ValidationError("User is already a participant in this event.")
        
        return data