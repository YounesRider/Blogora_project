from django.urls import path
from . import views

app_name = "interactions"

urlpatterns = [
    path("reaction/<int:article_id>/<str:reaction_type>/", views.toggle_reaction, name="toggle_reaction"),
    path("like/<int:article_id>/", views.toggle_like, name="toggle_like"),
    path("save/<int:article_id>/", views.toggle_save, name="toggle_save"),
    path("reactions/<int:article_id>/", views.get_article_reactions, name="get_reactions"),
]
