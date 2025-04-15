from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from . import views


urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', views.RegisterView.as_view(), name="register_new_user"),
    path('login/', views.LoginView.as_view(), name="login_user"),
    path('logout/', views.LogoutView.as_view(), name="logout_user"),
    path('password/reset/', views.PasswordResetRequestView.as_view(), name="reset_password_request"),
    path('password/reset/confirm/', views.PasswordResetConfirmView.as_view(), name="reset_password_confirm"),
    path('user/profile/<int:pk>/', views.ProfileView.as_view(), name="user_profile"),
    path('user/profile/', views.ProfileListView.as_view(), name="profile_list"),
]