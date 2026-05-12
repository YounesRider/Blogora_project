from django.urls import path
from . import views

app_name = 'taxonomy'

urlpatterns = [
    path('search/', views.tag_search, name='tag_search'),
]
