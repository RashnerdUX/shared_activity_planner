from django.shortcuts import render
from django.contrib.auth import authenticate
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

from rest_framework import generics, response, request, status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView


from .serializers import UserSerializer

#This variable stores the current auth model user
User = get_user_model()

# Create your views here.

#class UserView(APIView):
    #def getUser()


#For registering new users
class RegisterView(APIView):

    permission_classes = [permissions.AllowAny]
    def post(self, request):
        user = UserSerializer(data=request.data)
        if user.is_valid():
            user.save()
            return response.Response(data=user.data, status=status.HTTP_201_CREATED)
        return response.Response(data=user.errors, status=status.HTTP_400_BAD_REQUEST)
    
#For logging in users with their username and password
class LoginWithUsernameView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        username = request.data.get('username')
        password = request.data.get('username')

        #This will be the identifier used in the authentication
        user_identifier = None

        if email and not username:
            try:
                get_user = User.objects.get(email=email)
                user_identifier = getattr(object=get_user, name='username')
            except User.DoesNotExist:
                return response.Response(data={"message":"User does not exist"}, status=status.HTTP_404_NOT_FOUND)
            except User.MultipleObjectsReturned:
                return response.Response(data={"message":f"Too many users with {username}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            user_identifier = username

        if not user_identifier or not password:
             return response.Response({'error': 'Please provide username/email and password'}, status=status.HTTP_400_BAD_REQUEST)

        authenticated_user = authenticate(username=user_identifier, password=password)

        if authenticated_user:
            refresh = RefreshToken.for_user(authenticated_user)
            return response.Response(data={
                'refresh_token': str(refresh),
                'access_token': str(refresh.access_token)
            }, status=status.HTTP_200_OK)
        else:
            return response.Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
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
        
#This is the custom Token View for anyone that plans to use it
