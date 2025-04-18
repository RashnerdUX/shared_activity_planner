from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

from rest_framework import response, status
from rest_framework.views import APIView

from ..serializers import (PasswordResetConfirmSerializer, PasswordResetRequestSerializer,)

#This variable stores the current auth model user
User = get_user_model()

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
