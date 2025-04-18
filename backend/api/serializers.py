#import pytz

from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings

from .models import UserProfile, FriendsList, FriendRequest

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
    id = serializers.IntegerField(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(read_only=True, source='user_id.id')
    profile_image = serializers.CharField()
    bio = serializers.CharField()
    notification_preferences = serializers.JSONField()
    timezone = serializers.CharField()
    default_availability = serializers.JSONField()

    def create(self, validated_data):
        return UserProfile.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.profile_image = validated_data.get('profile_image', instance.profile_image)
        instance.bio = validated_data.get('bio', instance.bio)
        instance.notification_preferences = validated_data.get('notification_preferences', instance.notification_preferences)
        instance.timezone = validated_data.get('timezone', instance.timezone)
        instance.default_availability = validated_data.get('default_availability', instance.default_availability)
        instance.save()
        return instance
    
    """
    def validate_timezone(self, value):
        if value not in pytz.all_timezones:
            raise serializers.ValidationError(f"{value} is not a valid timezone.")
        return value
    """
    # TODO: Write logic to validate notification preferences and default_availability 
    
    def validate(self, attrs):
        return super().validate(attrs)
    
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists:
            raise serializers.ValidationError("No user found with this email address.")
        return value
    
    def save(self):
        user_email = self.validated_data['email']
        user = User.objects.get(email=user_email)
        if user.is_active:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = f"{settings.PASSWORD_RESET_CONFIRM_URL}/?uid:{uid}&token:{token}"

            print(reset_url)

            """
            send_mail(
            'Password Reset Request',
            f'Please click the following link to reset your password: {reset_url}',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
            )
            """

class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError("The two password fields didn't match.")
        try:
            uid = force_bytes(urlsafe_base64_decode(data['uid'])).decode()
            self.user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError("Invalid user ID.")

        if not default_token_generator.check_token(self.user, data['token']):
            raise serializers.ValidationError("Invalid reset token.")

        return data

    def save(self):
        self.user.set_password(self.validated_data['new_password'])
        self.user.save()


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
