from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('collections/', views.CollectionListView.as_view(), name='collection_list'),
    path('collections/<int:pk>/', views.CollectionDetailView.as_view(), name='collection_detail'),
    path('collections/create/', views.CollectionCreateView.as_view(), name='collection_create'),
    path('collections/<int:pk>/edit/', views.CollectionUpdateView.as_view(), name='collection_update'),
    path('collections/<int:pk>/delete/', views.CollectionDeleteView.as_view(), name='collection_delete'),
    path('collections/add/<int:article_id>/<int:collection_id>/', views.add_to_collection, name='add_to_collection'),
    path('collections/article/<int:article_id>/', views.get_user_collections, name='get_collections'),
    path('saved/', views.saved_articles, name='saved_articles'),
]
