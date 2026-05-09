from django.urls import path
from . import views

app_name = 'admin'

urlpatterns = [
    path('', views.AdminDashboardView.as_view(), name='dashboard'),
    path('users/', views.AdminUsersView.as_view(), name='users'),
    path('users/<int:pk>/', views.AdminUserDetailView.as_view(), name='user_detail'),
    path('articles/', views.AdminArticlesView.as_view(), name='articles'),
    path('articles/<int:pk>/', views.AdminArticleDetailView.as_view(), name='article_detail'),
    path('articles/<int:pk>/approve/', views.admin_approve_article, name='approve_article'),
    path('articles/<int:pk>/reject/', views.admin_reject_article, name='reject_article'),
    path('users/<int:pk>/toggle-role/', views.admin_toggle_user_role, name='toggle_user_role'),
]
