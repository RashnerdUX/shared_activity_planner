import re

from rest_framework import serializers
from django.db import transaction

from api.models import Comment, Event, CustomUser
from api.tasks import notify_mentions


class CommentEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ["id", "title"]

class CommentUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["id", "username", "content", "created_at"]
        read_only_fields = ["id", "created_at"]


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["id", "event", "user", "content", "created_at"]
        read_only_fields = ["user", "created_at"]

    def create(self, validated_data):
        event = validated_data["event"]
        content = validated_data["content"]
        user = self.context['request'].user
        comment = Comment.objects.create(
            event = event,
            user = user,
            content = content,
        )

        content = validated_data.get("content")
        pattern = r'@[\w-]+'
        mentioned_users = []
        usernames = [u[1:] for u in re.findall(pattern,content)]
        usernames = list(set(usernames) - {user.username})

        if usernames:
            notify_mentions.delay(mentioned_users=usernames, comment_user_username=user.username, comment_content = content)
        return comment