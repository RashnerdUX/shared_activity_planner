from django.conf import settings
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model


#This will get the user model used
User = get_user_model()


#This will help me to authenticate with email
class EmailBackend(BaseBackend):

    def get_user(self, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
        return user
    
    def authenticate(self, request, username = None, email = None, password = None, **kwargs):   
        user = None

        #Authenticate with email first
        if email:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return None
        
        #Authenticate with username if email didn't bring any user
        if not user and username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return None
            
        #If user is still none, return none
        if not user:
            return None
            
        #If a user was found, check the user and his password
        if user and user.check_password(password):
            return user
        else:
            return None

        