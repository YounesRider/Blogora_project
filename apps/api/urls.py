from django.urls import path
from . import views

app_name = "api"

urlpatterns = [
    path("onboarding/categories/", views.onboarding_categories, name="onboarding_categories"),
    path("recommendations/", views.my_recommendations, name="my_recommendations"),
]
