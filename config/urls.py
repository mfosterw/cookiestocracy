"""Base URL configuration"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include
from django.urls import path
from django.urls import reverse_lazy
from django.views import defaults as default_views
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView
from drf_spectacular.views import SpectacularSwaggerView

urlpatterns = [
    path(
        "about/", TemplateView.as_view(template_name="pages/about.html"), name="about"
    ),
    path(
        "privacy/",
        TemplateView.as_view(template_name="pages/privacy.html"),
        name="privacy",
    ),
    # User management
    path("users/", include("democrasite.users.urls", namespace="users")),
    path("accounts/", include("allauth.urls")),
    # ActivityPub
    path(
        "activitypub/", include("democrasite.activitypub.urls", namespace="activitypub")
    ),
    # webiscite
    path("", include("democrasite.webiscite.urls", namespace="webiscite")),
    # Media files
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
    path("", include("django_prometheus.urls")),
]

# API URLS
urlpatterns += [
    # API base url
    path("api/", include("config.api_router")),
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="api-schema"),
        name="api-docs",
    ),
]


if settings.DEBUG:
    # Django Admin, use {% url 'admin:index' %}
    # Admin site is only enabled during development
    urlpatterns += [path(settings.ADMIN_URL, admin.site.urls)]
    # Overwrite view site link because it points to the production url instead of local
    admin.AdminSite.site_url = reverse_lazy("webiscite:index")  # type: ignore[assignment]

    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls)), *urlpatterns]
