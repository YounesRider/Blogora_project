from django.urls import path
from . import views

app_name = "comments"

urlpatterns = [
    path("create/<int:article_id>/", views.create_comment, name="create"),
    path("like/<int:comment_id>/", views.like_comment, name="like"),
    path("edit/<int:comment_id>/", views.edit_comment, name="edit"),
    path("delete/<int:comment_id>/", views.delete_comment, name="delete"),
    path("thread/<int:comment_id>/", views.comment_thread, name="thread"),
]
