from django.urls import path
from . import views

app_name = "interactions"

urlpatterns = [
    path("like/article/<int:article_id>/", views.like_article, name="like_article"),
    path("reaction/<int:article_id>/<str:reaction_type>/", views.toggle_reaction, name="toggle_reaction"),
    path("reactions/<int:article_id>/", views.get_article_reactions, name="get_article_reactions"),
    path("like/comment/<int:comment_id>/", views.like_comment, name="like_comment"),
    path("save/article/<int:article_id>/", views.save_article, name="save_article"),
    path("likes/", views.get_user_likes, name="user_likes"),
]
