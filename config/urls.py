from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from apps.users.views import signup_view

urlpatterns = [
    # Blog
    path("", include("apps.blog.urls")),
    
    # Users - Notre vue d'inscription personnalisée d'abord
    path("account/signup/", signup_view, name="account_signup"),
    path("accounts/", include("allauth.urls")),
    path("users/", include("apps.users.urls")),
    
    # Comments
    path("comments/", include("apps.comments.urls")),
    
    # Interactions
    path("interactions/", include("apps.interactions.urls")),
    path("dashboard/", include("apps.dashboard.urls", namespace="dashboard")),
    path("comments/", include("apps.comments.urls", namespace="comments")),

    # API v1
    path("api/v1/", include("apps.api.urls", namespace="api")),

    # OpenAPI docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]

# Dev extras
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
