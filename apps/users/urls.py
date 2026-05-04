from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("signup/", views.signup_view, name="custom_signup"),
]
