from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model

from .models import UserProfile

#This sets the user variable to current User model
User = get_user_model()

#serializer for User
class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    date_joined = serializers.DateTimeField(read_only=True)

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
    
    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.username = validated_data.get('username', instance.username)
        instance.save()
        return instance


class ProfileSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(read_only=True)
    profile_image = serializers.CharField()
    bio = serializers.CharField()
    notification_preferences = serializers.JSONField()
    timezone = serializers.CharField()
    default_availability = serializers.CharField()

    def create(self, validated_data):
        return UserProfile.objects.create(validated_data)
    
    def update(self, instance, validated_data):
        instance.profile_image = validated_data.get('profile_image', instance.profile_image)
        instance.bio = validated_data.get('bio', instance.bio)
        instance.notification_preferences = validated_data.get('notification_preferences', instance.notification_preferences)
        instance.timezone = validated_data.get('timezone', instance.timezone)
        instance.default_availability = validated_data.get('default_availability', instance.default_availability)
        instance.save()
        return instance
    
    def validate(self, attrs):
        return super().validate(attrs)