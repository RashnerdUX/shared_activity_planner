from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model

from rest_framework import response, status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiTypes
from rest_framework_simplejwt import serializers

from ..serializers import (UserSerializer)

#This variable stores the current auth model user
User = get_user_model()

class RegisterView(APIView):
    """
    This endpoint is used to register and create a user for the shared planner app
    Once a user is created, there's a post-save signal that creates a friendlist table in the db for the specific user
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=UserSerializer,
        responses={
            201: UserSerializer,
            400: OpenApiTypes.OBJECT 
        }
    )
    def post(self, request):
        user = UserSerializer(data=request.data)
        if user.is_valid():
            user.save()
            return response.Response(data=user.data, status=status.HTTP_201_CREATED)
        return response.Response(data=user.errors, status=status.HTTP_400_BAD_REQUEST)
    
#This allows user to login with either username or email and password
#This will also include Oauth2 if possible
class LoginView(APIView):
    """
    This endpoint is used to login a user for the shared planner app
    It will create a Refresh token that lasts 24 hours and a corresponding Access Token that lasts an hour
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=serializers.TokenObtainPairSerializer,
        responses={
            201: serializers.TokenObtainPairSerializer,
            400: OpenApiTypes.OBJECT 
        }
    )
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
    """
    This endpoint logs a user out and denies them access to any view that requires authorization
    This endpoint will blacklist a Refreshtoken and prevent it from being used to create an access token again
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        request=serializers.TokenBlacklistSerializer,
        responses={
            201: serializers.TokenBlacklistSerializer,
            400: OpenApiTypes.OBJECT 
        }
    )
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return response.Response({"success": "Successfully logged out"}, status=status.HTTP_200_OK)
        except Exception as e:
            return response.Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
