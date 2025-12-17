from django.contrib.auth import get_user_model
from django.http import Http404

from rest_framework import response, status, permissions
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from ..serializers import (ProfileSerializer)
from ..models import (UserProfile)

#This variable stores the current auth model user
User = get_user_model()

class ProfileListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProfileSerializer

    @extend_schema(operation_id='list_profiles', responses={200: ProfileSerializer(many=True)})
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

    @extend_schema(request=ProfileSerializer, responses={201: None})
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
    serializer_class = ProfileSerializer

    def get_object(self, pk):
        try:
            user_profile = UserProfile.objects.get(id=pk)
            return user_profile
        except:
            raise Http404

    @extend_schema(operation_id='get_profile', responses={200: ProfileSerializer})
    def get(self,request, pk):
        try:
            user_profile = self.get_object(pk)
            serialized = ProfileSerializer(instance=user_profile)
            return response.Response(data=serialized.data, status=status.HTTP_200_OK)
        except:
            return response.Response(data={"message":"User Profile does not exist"}, status=status.HTTP_404_NOT_FOUND)
    
    @extend_schema(request=ProfileSerializer, responses={200: None})
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
    
    @extend_schema(request=ProfileSerializer, responses={200: None})
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