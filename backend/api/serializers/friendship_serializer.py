from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model

from ..models import FriendsList, FriendRequest
from ..serializers import UserSerializer

#This sets the user variable to current User model
User = get_user_model()

class FriendsListSerializer(serializers.Serializer):
    user = UserSerializer(read_only=True)
    friends = UserSerializer(read_only=True, many=True)

    def create(self, validated_data):
        return FriendsList.objects.create(**validated_data)
    
    def validate(self, data):
        request = self.context.get('request')
        if data["user"] != request.user:
            raise serializers.ValidationError("Authenticated User is not making the request")
        return data
    
class FriendRequestSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    sender = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)
    receiver_id = serializers.IntegerField(write_only=True)
    status = serializers.CharField()

    def validate(self, data):
        request = self.context.get('request')
        receiver_id = data["receiver_id"]

        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("User can not add itself")
        
        sender = request.user
        receiver = None

        try:
            receiver = User.objects.get(id=receiver_id)
        except User.DoesNotExist:
            raise serializers.ValidationError("Receiver does not exist")

        #Check if user is adding himself
        if sender == receiver:
            raise serializers.ValidationError("User can not add itself")
        
        #Check if user already sent a request
        if FriendRequest.objects.filter(
            sender=sender,
            receiver=receiver,
            status='P'
        ).exists():
            raise serializers.ValidationError("A pending friend request already exists")
        
        #Check if user is already friends with them
        sender_friends = FriendsList.objects.get(user=sender)
        if receiver in sender_friends.friends.all():
            raise serializers.ValidationError("You are already friends with this user")

        data["sender"] = sender
        data["receiver"] = receiver
        data["status"] = "P"
    
        return data

    def create(self, validated_data):
        return FriendRequest.objects.create(**validated_data)
    
    def update(self,instance, validated_data):
        instance.status = validated_data.get("status", instance.status)
        instance.save()
        return instance
