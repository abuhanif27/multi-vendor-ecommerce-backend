"""Root URL configuration for the ecommerce API."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from apps.api.views import HealthCheckAPIView


def api_landing_page(request):
    return JsonResponse(
        {
            "name": "Multi-Vendor E-commerce Backend API",
            "version": "v1",
            "api": "/api/v1/",
            "docs": "/docs/",
            "redoc": "/redoc/",
            "schema": "/schema/",
            "health": "/health/",
        }
    )


api_v1_urlpatterns = [
    path("", include("apps.api.urls")),
    path("auth/", include("apps.accounts.urls")),
    path("", include("apps.shops.urls")),
    path("", include("apps.catalog.urls")),
    path("", include("apps.inventory.urls")),
    path("cart/", include("apps.cart.urls")),
    path("checkout/", include("apps.checkout.urls")),
    path("", include("apps.orders.urls")),
    path("", include("apps.payments.urls")),
    path("", include("apps.shipping.urls")),
    path("", include("apps.notifications.urls")),
    path("", include("apps.reviews.urls")),
    path("", include("apps.promotions.urls")),
    path("analytics/", include("apps.analytics.urls")),
    path("admin/", include("apps.administration.api.urls")),
]


urlpatterns = [
    path("", api_landing_page, name="api-landing-page"),
    path("admin/", admin.site.urls),
    path("health/", HealthCheckAPIView.as_view(), name="health-check-root"),
    path("api/v1/", include(api_v1_urlpatterns)),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
