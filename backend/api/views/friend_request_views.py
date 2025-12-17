from django.contrib.auth import get_user_model
from django.db.models import Q
from drf_spectacular.utils import extend_schema

from rest_framework import response,status, permissions
from rest_framework.views import APIView

from ..serializers import (FriendRequestSerializer)
from ..models import (FriendRequest, FriendsList)

#This variable stores the current auth model user
User = get_user_model()

class FriendRequestListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FriendRequestSerializer

    @extend_schema(responses={200: FriendRequestSerializer(many=True)})
    def get(self, request):
        user = request.user
        requests = FriendRequest.objects.filter(
            Q(receiver=user, status='P') | Q(sender=user)
        )
        serializer = FriendRequestSerializer(requests, many=True)
        return response.Response(serializer.data, status=status.HTTP_200_OK)
        
class SendFriendRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FriendRequestSerializer

    @extend_schema(request=FriendRequestSerializer, responses={200: None})
    def post(self, request):
        serialized = FriendRequestSerializer(data=request.data, context={'request': request})
        if serialized.is_valid():
            serialized.save()
            return response.Response(data={"message":"Friend Request successfully sent"}, status=status.HTTP_200_OK)
        return response.Response(serialized.errors, status=status.HTTP_400_BAD_REQUEST)

class AcceptFriendRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FriendRequestSerializer

    @extend_schema(request=None, responses={200: None})
    def post(self, request, pk):
        try:
            friend_request = FriendRequest.objects.get(
                id=pk,
                receiver=request.user,
                status='P'
            )
            if friend_request.accept_request():
                return response.Response(
                    {"message": "Friend request accepted"},
                    status=status.HTTP_200_OK
                )
            return response.Response(
                {"message": "Cannot accept request"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except FriendRequest.DoesNotExist:
            return response.Response(
                {"message": "Friend request not found or not pending"},
                status=status.HTTP_404_NOT_FOUND
            )

class DenyFriendRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FriendRequestSerializer

    @extend_schema(request=None, responses={200: None})
    def post(self, request, pk):
        try:
            friend_request = FriendRequest.objects.get(
                id=pk,
                receiver=request.user,
                status='P'
            )
            if friend_request.deny_request():
                return response.Response(
                    {"message": "Friend request denied"},
                    status=status.HTTP_200_OK
                )
            return response.Response(
                {"message": "Cannot deny request"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except FriendRequest.DoesNotExist:
            return response.Response(
                {"message": "Friend request not found or not pending"},
                status=status.HTTP_404_NOT_FOUND
            )

class UnfriendView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FriendRequestSerializer

    @extend_schema(request=None, responses={200: None})
    def post(self, request, user_id):
        try:
            removee = User.objects.get(id=user_id)
            friends_list = FriendsList.objects.get(user=request.user)
            if friends_list.unfriend(removee):
                return response.Response(
                    {"message": f"Unfriended {removee.username}"},
                    status=status.HTTP_200_OK
                )
            return response.Response(
                {"message": "Cannot unfriend (not friends or same user)"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except User.DoesNotExist:
            return response.Response(
                {"message": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except FriendsList.DoesNotExist:
            return response.Response(
                {"message": "Friends list not found"},
                status=status.HTTP_404_NOT_FOUND
            )
