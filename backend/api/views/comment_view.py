from rest_framework import views, generics, permissions

from api.models import Comment
from api.serializers import CommentSerializer
from api.permissions import CanCommentInEvent

class EventCommentsView(generics.ListCreateAPIView):
    """
    This is the view for getting the list of comments for a particular event and for creating a comment in the dicussion forum of an event
    """
    queryset = Comment
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

class CommentView(generics.RetrieveDestroyAPIView):
    """
    This is the view for getting a single comment and deleting it. Only the person who created the event can delete it
    """
    queryset = Comment
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]