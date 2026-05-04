from django.urls import path
from . import views

app_name = "blog"

urlpatterns = [
    path("", views.home, name="home"),
    path("articles/", views.ArticleListView.as_view(), name="article_list"),
    path("article/<slug:slug>/", views.ArticleDetailView.as_view(), name="detail"),
    path("category/<slug:category_slug>/", views.ArticleListView.as_view(), name="category"),
    path("tag/<slug:tag_slug>/", views.ArticleListView.as_view(), name="tag"),
    path("create/", views.ArticleCreateView.as_view(), name="create"),
    path("my-articles/", views.MyArticlesView.as_view(), name="my_articles"),
    path("edit/<slug:slug>/", views.ArticleUpdateView.as_view(), name="update"),
    path("delete/<int:pk>/", views.ArticleDeleteView.as_view(), name="delete"),
]
