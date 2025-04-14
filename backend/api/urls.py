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
    path('login-username-only/', views.LoginWithUsernameView.as_view(), name="Default backend login"),
    path('logout/', views.LogoutView.as_view(), name="Logout User"),
]
