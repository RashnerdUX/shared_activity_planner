from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from api import views


urlpatterns = [
    #JWT Tokens View
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    #Path to Auth views
    path('register/', views.RegisterView.as_view(), name="register_new_user"),
    path('login/', views.LoginView.as_view(), name="login_user"),
    path('logout/', views.LogoutView.as_view(), name="logout_user"),
    path('password/reset/', views.PasswordResetRequestView.as_view(), name="reset_password_request"),
    path('password/reset/confirm/', views.PasswordResetConfirmView.as_view(), name="reset_password_confirm"),
    #Path to Profile views
    path('user/profile/<int:pk>/', views.ProfileView.as_view(), name="user_profile"),
    path('user/profile/', views.ProfileListView.as_view(), name="profile_list"),
    #Path to Friends system views
    path('user/friends/', views.FriendListView.as_view(), name="user_friends"),
    path('user/friend_requests/', views.FriendRequestListView.as_view(), name="user_friend_requests"),
    path('user/friend_request/send/', views.SendFriendRequestView.as_view(), name="send_friend_request"),
    path('user/friend_request/<int:pk>/accept/', views.AcceptFriendRequestView.as_view(), name="accept_friend_request"),
    path('user/friend_request/<int:pk>/deny/', views.DenyFriendRequestView.as_view(), name="deny_friend_request"),
    path('user/friends/unfriend/<int:user_id>/', views.UnfriendView.as_view(), name="unfriend_user"),
    #Path to Events and Groups
    path('user/group/events/', views.EventListView.as_view(), name="list_of_events"),
    path('user/group/event/<int:pk>/', views.EventView.as_view(), name="details_of_event"),
    path('user/groups/', views.GroupListView.as_view(), name='group_list'),
    path('user/groups/<int:pk>/', views.GroupDetailView.as_view(), name='group_details'),
    path('user/groups/<int:pk>/members/', views.GroupMembersView.as_view(), name='group_members'),
    #Path to Time and scheduling
    path('event/<int:pk>/scheduling/', views.TimeOptionView.as_view(), name="event_scheduling"),
    path('event/scheduling/', views.TimeOptionListView.as_view(), name="list_of_event_time" ),
    path('event/<int:pk>/vote/', views.TimeVotingView.as_view(), name="time_voting"),
    path('event/vote/<int:pk>/', views.TimeVotingView.as_view(), name="modify_time_vote"),
    path('event/<int:pk>/vote_count/', views.GetTimeVotesView.as_view(), name="time_vote_count"),
    path('event/<int:pk>/set_final_time/', views.ScheduleEventView.as_view(), name="set_final_time"),
    #Path to Participants and Invitation
    path('events/<int:pk>/participant/', views.ParticipantView.as_view(), name="event_participants"),
    path('events/<int:pk>/invite/', views.InvitationView.as_view(), name="send_invites"),
    #Path to Task and Task Categories
    path('event/tasks/', views.TaskListView.as_view(), name='task_list'),
    path('event/tasks/<int:pk>/', views.TaskView.as_view(), name='task_detail'), 
    path('event/tasks/<int:pk>/assign/', views.TaskAssignmentView.as_view(), name='task_assign'),
    path('event/tasks/<int:pk>/status/', views.ChangeTaskStatusView.as_view(), name='task_status'),
    path('event/task-categories/', views.TaskCategoryListView.as_view(), name='task_category_list'),
    path('event/task-categories/<int:pk>/', views.TaskCategoryView.as_view(), name='task_category_detail'),
    #Path to Comment and Notifications
    path("event/comments/", views.EventCommentsView.as_view(), name="event_comments"),
    path("user/notifications/", views.UserNotificationsView.as_view(), name="user_notifcations"),
    path("notifications/<int:pk>/read/", views.MarkNotificationAsReadView.as_view(), name="mark_notification_as_read"),
    path("notifications/read_all/", views.MarkAllNotificationsAsReadView.as_view(), name="mark_all_notifications_as_read"),
    path("notifications/preferences/", views.NotificationPreferenceListUpdateView.as_view(), name="notification_preferences"),
]