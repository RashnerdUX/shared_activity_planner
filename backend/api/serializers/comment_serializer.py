import re

from rest_framework import serializers
from django.db import transaction

from api.models import Comment, Event, CustomUser
from api.tasks import notify_mentions
from api.signals import comment_created


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["id", "event", "user", "content", "parent", "created_at"]
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

        #This sends the following resources to the receiver after a comment is created
        comment_created.send(
            sender=comment.__class__,
            comment=comment,
        )

        return comment