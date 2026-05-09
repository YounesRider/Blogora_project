from django.urls import path
from . import views

app_name = "comments"

urlpatterns = [
    path("create/<int:article_id>/", views.create_comment, name="create_comment"),
    path("edit/<int:comment_id>/", views.edit_comment, name="edit_comment"),
    path("delete/<int:comment_id>/", views.delete_comment, name="delete_comment"),
    path("thread/<int:comment_id>/", views.comment_thread, name="thread"),
]
