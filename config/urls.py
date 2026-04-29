from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),

    # Auth (allauth)
    path("accounts/", include("allauth.urls")),

    # Apps
    path("", include("apps.blog.urls", namespace="blog")),
    path("users/", include("apps.users.urls", namespace="users")),
    path("dashboard/", include("apps.dashboard.urls", namespace="dashboard")),

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
