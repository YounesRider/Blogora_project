from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='list'),
    path('dropdown/', views.notification_dropdown, name='dropdown'),
    path('mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_read'),
    path('mark-all-read/', views.mark_all_notifications_read, name='mark_all_read'),
    path('delete/<int:notification_id>/', views.delete_notification, name='delete'),
    path('preferences/', views.notification_preferences, name='preferences'),
]
