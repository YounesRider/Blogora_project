from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from apps.users.views import signup_view, logout_view

urlpatterns = [
    # Admin
    path("admin/", include("apps.admin.urls", namespace="admin")),
    
    # Blog
    path("", include("apps.blog.urls")),
    
    # Core (Collections)
    path("collections/", include("apps.core.urls", namespace="core")),
    
    # Users - custom signup and logout views
    path("accounts/signup/", signup_view, name="account_signup"),
    path("account/signup/", RedirectView.as_view(url="/accounts/signup/", permanent=False)),
    path("accounts/logout/", logout_view, name="account_logout"),
    path("account/logout/", RedirectView.as_view(url="/accounts/logout/", permanent=False)),
    path("accounts/", include("allauth.urls")),
    path("users/", include("apps.users.urls")),
    
    # Comments
    path("comments/", include("apps.comments.urls")),
    
    # Interactions
    path("interactions/", include("apps.interactions.urls")),
    
    # Notifications
    path("notifications/", include("apps.notifications.urls", namespace="notifications")),
    
    # Recommendations
    path("recommendations/", include("apps.recommendations.urls", namespace="recommendations")),
    
    # Dashboard
    path("dashboard/", include("apps.dashboard.urls", namespace="dashboard")),

    # API v1
    path("api/v1/", include("apps.api.urls", namespace="api")),
    
    # Taxonomy API
    path("api/tags/", include("apps.taxonomy.urls", namespace="taxonomy")),

    # OpenAPI docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]

# Dev extras
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
