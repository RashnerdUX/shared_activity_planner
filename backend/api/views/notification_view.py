from rest_framework import generics, permissions, response, status, views
from drf_spectacular.utils import extend_schema

from api.models import Notification, NotificationPreference
from api.serializers import NotificationSerializer, NotificationPreferenceSerializer


class UserNotificationsView(generics.ListCreateAPIView):
    """
    This retrieves a list of notifications for a particular user, excluding the comments where they have been tagged.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')
    
class MarkNotificationAsReadView(views.APIView):
    """
    This allows a user to mark a notification as read
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer

    @extend_schema(request=None, responses={200: None})
    def post(self, request, pk):
        try:
            notification = Notification.objects.get(id=pk, user=request.user)
            if notification.mark_as_read():
                return response.Response({"message": "Notification marked as read."}, status=status.HTTP_200_OK)
            else:
                return response.Response({"message": "Notification failed to be marked as read."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Notification.DoesNotExist:
            return response.Response({"message": "Notification not found."}, status=status.HTTP_404_NOT_FOUND)
        
class MarkAllNotificationsAsReadView(views.APIView):
    """
    This allows a user to mark all his notifications as read
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer

    @extend_schema(request=None, responses={200: None})
    def post(self, request):
        try:
            updated_count = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
            return response.Response({"message": f"{updated_count} notifications marked as read."}, status=status.HTTP_200_OK)
        except Exception as e:
            return response.Response({"message": f"There was an error marking all of {request.user.username}'s notifications", "error":f"{e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class NotificationPreferenceListUpdateView(generics.ListCreateAPIView):
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return NotificationPreference.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
