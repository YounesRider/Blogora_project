from django.urls import path
from . import views

app_name = 'admin'

urlpatterns = [
    # Admin Dashboard & Articles
    path('', views.AdminDashboardView.as_view(), name='dashboard'),
    path('articles/', views.AdminArticlesView.as_view(), name='articles'),
    path('articles/<int:pk>/', views.AdminArticleDetailView.as_view(), name='article_detail'),
    path('articles/<int:pk>/approve/', views.admin_approve_article, name='approve_article'),
    path('articles/<int:pk>/reject/', views.admin_reject_article, name='reject_article'),
    path('articles/<int:pk>/delete/', views.admin_delete_article, name='delete_article'),
    
    # Admin Users Management
    path('users/', views.AdminUsersView.as_view(), name='users'),
    path('users/<int:pk>/', views.AdminUserDetailView.as_view(), name='user_detail'),
    path('users/<int:pk>/delete/', views.admin_delete_user, name='delete_user'),
    path('users/<int:pk>/toggle-role/', views.admin_toggle_user_role, name='toggle_user_role'),
    path('users/<int:pk>/auto-publish/', views.admin_set_auto_publish, name='set_auto_publish'),
    
    # Admin Moderators Management
    path('moderators/', views.AdminModeratorsView.as_view(), name='moderators'),
    path('moderators/<int:pk>/', views.AdminModeratorDetailView.as_view(), name='moderator_detail'),
    path('users/<int:pk>/create-moderator/', views.admin_create_moderator, name='create_moderator'),
    path('moderators/<int:pk>/delete/', views.admin_delete_moderator, name='delete_moderator'),
    path('moderators/<int:pk>/toggle-permission/<str:permission>/', views.admin_toggle_moderator_permission, name='toggle_moderator_permission'),
    path('moderators/<int:pk>/toggle-active/', views.admin_toggle_moderator_active, name='toggle_moderator_active'),
    
    # Moderator Content Review
    path('moderation/', views.ModeratorDashboardView.as_view(), name='moderation_dashboard'),
    path('moderation/articles/', views.ModeratorArticlesView.as_view(), name='moderation_articles'),
    path('moderation/articles/<int:pk>/approve/', views.moderator_approve_article, name='moderator_approve_article'),
    path('moderation/articles/<int:pk>/reject/', views.moderator_reject_article, name='moderator_reject_article'),
    path('moderation/articles/<int:pk>/delete/', views.moderator_delete_article, name='moderator_delete_article'),
    path('moderation/articles/bulk-approve/', views.moderator_bulk_approve_articles, name='moderator_bulk_approve_articles'),
    path('moderation/articles/bulk-reject/', views.moderator_bulk_reject_articles, name='moderator_bulk_reject_articles'),
    path('moderation/articles/bulk-delete/', views.moderator_bulk_delete_articles, name='moderator_bulk_delete_articles'),
    path('moderation/comments/', views.ModeratorCommentsView.as_view(), name='moderation_comments'),
    path('moderation/comments/<int:pk>/approve/', views.moderator_approve_comment, name='moderator_approve_comment'),
    path('moderation/comments/<int:pk>/delete/', views.moderator_delete_comment, name='moderator_delete_comment'),
]
