from django.shortcuts import render
from django.contrib.auth import authenticate
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.http import Http404
from django.db.models import Q

from rest_framework import generics, response, request, status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView


from .serializers import (UserSerializer, PasswordResetConfirmSerializer, PasswordResetRequestSerializer, ProfileSerializer, FriendsListSerializer, FriendRequestSerializer)
from .models import (UserProfile, FriendRequest, FriendsList)

#This variable stores the current auth model user
User = get_user_model()

# Create your views here.
class ProfileListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            profiles = UserProfile.objects.all()
            serialized_profiles = ProfileSerializer(instance=profiles, many=True)
            return response.Response(data=serialized_profiles.data, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"Error in ProfileListView.get: {str(e)}")  # Log the actual error
            return response.Response(
                data={"message": f"Error retrieving profiles: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

    def post(self, request):
        serialized = ProfileSerializer(data=request.data)
        user = request.user
        if serialized.is_valid():
            print(user)
            serialized.save(user_id = user)
            return response.Response(data={"message":"User Profile is created"}, status=status.HTTP_201_CREATED)
        return response.Response(data={"message":"User Profile could not be created", "errors":f"{serialized.errors}"}, status=status.HTTP_400_BAD_REQUEST)
    

class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk):
        try:
            user_profile = UserProfile.objects.get(id=pk)
            return user_profile
        except:
            raise Http404

    def get(self,request, pk):
        try:
            user_profile = self.get_object(pk)
            serialized = ProfileSerializer(instance=user_profile)
            return response.Response(data=serialized.data, status=status.HTTP_200_OK)
        except:
            return response.Response(data={"message":"User Profile does not exist"}, status=status.HTTP_404_NOT_FOUND)
    
    def put(self, request, pk,):
        try:
            user_profile = self.get_object(pk)
            serialized = ProfileSerializer(instance=user_profile, data=request.data)
            if serialized.is_valid():
                serialized.save()
                return response.Response(data={"message":"User Profile is updated"}, status=status.HTTP_200_OK)
            else:
                return response.Response(data={"message":"User Profile could not be updated"}, status=status.HTTP_400_BAD_REQUEST)
        except:
            return response.Response(data={"message":"User Profile could not be found"}, status=status.HTTP_404_NOT_FOUND)
    
    def patch(self, request, pk):
        try:
            user_profile = self.get_object(pk)
            serialized = ProfileSerializer(instance=user_profile, data=request.data, partial=True)
            if serialized.is_valid():
                serialized.save()
                return response.Response(data={"message":"User Profile is updated"}, status=status.HTTP_200_OK)
            else:
                return response.Response(data={"message":"User Profile could not be updated"}, status=status.HTTP_400_BAD_REQUEST)
        except:
            return response.Response(data={"message":"User Profile could not be found"}, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, pk):
        try:
            user_profile = self.get_object(pk)
            user_profile.delete()
            return response.Response(data={"message":"User Profile was deleted"}, status=status.HTTP_200_OK)
        except:
            return response.Response(data={"message":"User Profile could not be found"}, status=status.HTTP_404_NOT_FOUND)


#For registering new users
class RegisterView(APIView):

    permission_classes = [permissions.AllowAny]
    def post(self, request):
        user = UserSerializer(data=request.data)
        if user.is_valid():
            user.save()
            return response.Response(data=user.data, status=status.HTTP_201_CREATED)
        return response.Response(data=user.errors, status=status.HTTP_400_BAD_REQUEST)
    
#This allows user to login with either username or email and password
#This will also include Oauth2 if possible
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email') or request.data.get('email_address')
        username = request.data.get('username')
        password = request.data.get('password')

        authenticated_user = None

        #Check if password was provided
        if not password:
            return response.Response(
            data={"message": "Password is required"}, 
            status=status.HTTP_400_BAD_REQUEST
            )

        #Check if email or username was created
        if not (email or username):
            return response.Response(
            data={"message": "Please provide email or username"}, 
            status=status.HTTP_400_BAD_REQUEST
            )

        # Try with email first if provided
        if email:
            authenticated_user = authenticate(request, email=email, password=password)
        
        # If email authentication failed or only username was provided
        if authenticated_user is None and username:
            authenticated_user = authenticate(request, username=username, password=password)
        
        if authenticated_user:
            refresh = RefreshToken.for_user(authenticated_user)
            return response.Response(data={
                'refresh_token': str(refresh),
                'access_token': str(refresh.access_token)
            }, status=status.HTTP_200_OK)
        else:
            return response.Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

#This will ensure User is logged out
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return response.Response({"success": "Successfully logged out"}, status=status.HTTP_200_OK)
        except Exception as e:
            return response.Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
#This is the view for resetting password
class PasswordResetRequestView(APIView):
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response({"message": "Password reset email sent successfully."}, status=status.HTTP_200_OK)

class PasswordResetConfirmView(APIView):
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response({"message": "Password reset successful."}, status=status.HTTP_200_OK)

class FriendListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            friends_object = FriendsList.objects.get(user=request.user)
            serialized = FriendsListSerializer(instance=friends_object)
            return response.Response(data=serialized.data, status=status.HTTP_200_OK)
        except friends_object.DoesNotExist:
            return response.Response(data={"message":"Friend List was not found"}, status=status.HTTP_404_NOT_FOUND)
        
class FriendRequestListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        requests = FriendRequest.objects.filter(
            Q(receiver=user, status='P') | Q(sender=user)
        )
        serializer = FriendRequestSerializer(requests, many=True)
        return response.Response(serializer.data, status=status.HTTP_200_OK)
        
class SendFriendRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serialized = FriendRequestSerializer(data=request.data, context={'request': request})
        if serialized.is_valid():
            serialized.save()
            return response.Response(data={"message":"Friend Request successfully sent"}, status=status.HTTP_200_OK)
        return response.Response(serialized.errors, status=status.HTTP_400_BAD_REQUEST)

class AcceptFriendRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

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
