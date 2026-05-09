from django.urls import path
from . import views

app_name = 'recommendations'

urlpatterns = [
    path('', views.recommendation_dashboard, name='dashboard'),
    path('refresh/', views.refresh_recommendations, name='refresh'),
    path('settings/', views.recommendation_settings, name='settings'),
    path('similar/<int:article_id>/', views.get_article_recommendations, name='similar'),
]
