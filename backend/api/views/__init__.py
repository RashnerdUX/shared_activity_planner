from .auth_views import RegisterView, LoginView, LogoutView
from .profile_views import ProfileListView, ProfileView
from .password_reset_views import PasswordResetConfirmView, PasswordResetRequestView
from .friend_list_views import FriendListView
from .friend_request_views import FriendRequestListView, SendFriendRequestView, AcceptFriendRequestView, DenyFriendRequestView, UnfriendView