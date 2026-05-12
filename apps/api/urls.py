from django.urls import path
from . import views

app_name = "api"

urlpatterns = [
    path("onboarding/categories/", views.onboarding_categories, name="onboarding_categories"),
    path("recommendations/", views.my_recommendations, name="my_recommendations"),
    path("track-reading/<int:article_id>/", views.track_reading, name="track_reading"),
    path("upload-inline-image/", views.upload_inline_image, name="upload_inline_image"),
]
