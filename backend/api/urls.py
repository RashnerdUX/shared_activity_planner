from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from . import views


urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', views.RegisterView.as_view(), name="Register a new user"),
    path('login/', views.LoginView.as_view(), name="Login User"),
    path('logout/', views.LogoutView.as_view(), name="Logout User"),
    path('password/reset/', views.PasswordResetRequestView.as_view(), name="Reset Password"),
    path('password/reset/confirm/', views.PasswordResetConfirmView.as_view(), name="Reset Password"),
    path('user/profile/<int:pk>/', views.ProfileView.as_view(), name="User Profile"),
    path('user/profile/', views.ProfileListView.as_view(), name="Profile List"),
]