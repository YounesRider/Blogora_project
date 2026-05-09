from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("profile/<str:username>/", views.user_profile, name="user_profile"),
    path("follow/<int:user_id>/", views.follow_user, name="follow_user"),
    path("following/", views.FollowingListView.as_view(), name="following"),
    path("followers/", views.FollowersListView.as_view(), name="followers"),
    path("signup/", views.signup_view, name="custom_signup"),
]
