from rest_framework import views, generics, permissions

from api.models import Comment
from api.serializers import CommentSerializer
from api.permissions import CanCommentInEvent, CanDeleteAComment

class EventCommentsView(generics.ListCreateAPIView):
    """
    This is the endpoint for getting the list of comments for a particular event and for creating a comment in the dicussion forum of an event. Only the user who is participating in an event can comment in the event so "event_id" is expected in the query params
    """
    queryset = Comment
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, CanCommentInEvent]

class CommentView(generics.RetrieveDestroyAPIView):
    """
    This is the endpoint for retrieving a single comment and deleting it.
    Only the owner of the comment, the creator of an event or one of the admins can do this
    """
    queryset = Comment
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, CanDeleteAComment]