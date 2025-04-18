from django.contrib.auth import get_user_model

from rest_framework import response, status, permissions
from rest_framework.views import APIView


from ..serializers import (FriendsListSerializer,)
from ..models import (FriendsList)

#This variable stores the current auth model user
User = get_user_model()

class FriendListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            friends_object = FriendsList.objects.get(user=request.user)
            serialized = FriendsListSerializer(instance=friends_object)
            return response.Response(data=serialized.data, status=status.HTTP_200_OK)
        except friends_object.DoesNotExist:
            return response.Response(data={"message":"Friend List was not found"}, status=status.HTTP_404_NOT_FOUND)
