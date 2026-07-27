import sys

import django
from django.conf import settings
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.serializers import HealthCheckSerializer


from drf_spectacular.utils import extend_schema, OpenApiResponse


def developer_portal(request):
    api_version = settings.SPECTACULAR_SETTINGS.get("VERSION", "v1")
    description_lines = [
        line.strip()
        for line in settings.SPECTACULAR_SETTINGS.get("DESCRIPTION", "").splitlines()
        if line.strip() and not line.strip().startswith("#") and not line.strip().startswith("-")
    ]
    environment = "Development" if settings.DEBUG else "Production"
    database_engine = settings.DATABASES["default"]["ENGINE"].rsplit(".", 1)[-1]
    base_url = request.build_absolute_uri("/").rstrip("/")

    quick_links = [
        {"label": "Swagger UI", "url": reverse("swagger-ui"), "style": "primary"},
        {"label": "ReDoc", "url": reverse("redoc"), "style": "secondary"},
        {"label": "OpenAPI Schema", "url": reverse("schema"), "style": "secondary"},
        {"label": "Health Check", "url": reverse("health-check-root"), "style": "secondary"},
        {"label": "Django Admin", "url": reverse("admin:index"), "style": "secondary"},
    ]

    module_cards = [
        {
            "name": "Authentication",
            "purpose": "Register users, issue JWT credentials, and verify email ownership.",
            "endpoints": ["/api/v1/auth/register/", "/api/v1/auth/login/", "/api/v1/auth/verify-email/"],
        },
        {
            "name": "Users",
            "purpose": "Expose authenticated user profile context for API clients.",
            "endpoints": ["/api/v1/me/"],
        },
        {
            "name": "Vendors",
            "purpose": "Support vendor onboarding and operational vendor administration.",
            "endpoints": ["/api/v1/my/shops/", "/api/v1/admin/vendors/{shop_id}/approve/"],
        },
        {
            "name": "Shops",
            "purpose": "Create, list, retrieve, and maintain vendor storefronts.",
            "endpoints": ["/api/v1/shops/", "/api/v1/shops/{slug}/", "/api/v1/my/shops/"],
        },
        {
            "name": "Categories",
            "purpose": "Organize catalog data through browsable product categories.",
            "endpoints": ["/api/v1/categories/", "/api/v1/categories/{slug}/"],
        },
        {
            "name": "Products",
            "purpose": "Publish and manage marketplace product listings.",
            "endpoints": ["/api/v1/products/", "/api/v1/products/{slug}/", "/api/v1/my/products/"],
        },
        {
            "name": "Product Variants",
            "purpose": "Represent purchasable SKUs with price, barcode, and status metadata.",
            "endpoints": ["/api/v1/shops/{shop_slug}/products/{product_slug}/variants/"],
        },
        {
            "name": "Inventory",
            "purpose": "Track stock levels and inventory transaction history per variant.",
            "endpoints": [
                "/api/v1/shops/{shop_slug}/products/{product_slug}/variants/{sku}/inventory/",
                "/api/v1/shops/{shop_slug}/products/{product_slug}/variants/{sku}/inventory/transactions/",
            ],
        },
        {
            "name": "Cart",
            "purpose": "Maintain buyer carts, cart items, quantities, and cart totals.",
            "endpoints": ["/api/v1/cart/", "/api/v1/cart/items/", "/api/v1/cart/items/{id}/"],
        },
        {
            "name": "Checkout",
            "purpose": "Validate cart state and prepare order creation from selected items.",
            "endpoints": ["/api/v1/checkout/"],
        },
        {
            "name": "Orders",
            "purpose": "Expose buyer orders and vendor-specific order fulfillment views.",
            "endpoints": ["/api/v1/orders/", "/api/v1/orders/{id}/", "/api/v1/vendor-orders/"],
        },
        {
            "name": "Payments",
            "purpose": "Initialize payments and receive asynchronous gateway webhooks.",
            "endpoints": ["/api/v1/payments/create/", "/api/v1/payments/webhooks/stripe/"],
        },
        {
            "name": "Refunds",
            "purpose": "Represent refund records created from payment and return workflows.",
            "endpoints": ["/api/v1/payments/create/", "/api/v1/payments/webhooks/stripe/"],
        },
        {
            "name": "Returns",
            "purpose": "Support post-order return flows through order domain records.",
            "endpoints": ["/api/v1/orders/", "/api/v1/vendor-orders/"],
        },
        {
            "name": "Shipping",
            "purpose": "Track shipments, assign couriers, and update delivery status.",
            "endpoints": ["/api/v1/shipping/my-shipments/", "/api/v1/shipping/shipments/{id}/"],
        },
        {
            "name": "Reviews",
            "purpose": "Capture product and shop feedback, reports, and moderation status.",
            "endpoints": ["/api/v1/product-reviews/", "/api/v1/shop-reviews/"],
        },
        {
            "name": "Notifications",
            "purpose": "Deliver and manage in-app notifications for authenticated users.",
            "endpoints": ["/api/v1/notifications/", "/api/v1/notifications/read-all/"],
        },
        {
            "name": "Promotions",
            "purpose": "Evaluate coupons, public promotions, and administrative promotion rules.",
            "endpoints": ["/api/v1/promotions/validate/", "/api/v1/admin/promotions/"],
        },
        {
            "name": "Analytics",
            "purpose": "Provide vendor dashboards and sales export workflows.",
            "endpoints": ["/api/v1/analytics/dashboard/", "/api/v1/analytics/export-sales/"],
        },
        {
            "name": "Administration",
            "purpose": "Moderate vendors, products, reviews, and platform promotions.",
            "endpoints": ["/api/v1/admin/vendors/{shop_id}/approve/", "/api/v1/admin/products/{product_id}/approve/"],
        },
    ]

    context = {
        "project_title": settings.SPECTACULAR_SETTINGS.get("TITLE", "Marketplace API"),
        "project_description": description_lines[0] if description_lines else "REST API developer portal.",
        "api_version": api_version,
        "environment": environment,
        "django_version": django.get_version(),
        "python_version": sys.version.split()[0],
        "database_engine": database_engine,
        "is_postgresql": "postgresql" in settings.DATABASES["default"]["ENGINE"],
        "jwt_authentication": "Enabled",
        "payment_gateways": ["Stripe", "SSLCommerz"],
        "tech_stack": [
            "Django",
            "Django REST Framework",
            "drf-spectacular",
            "Simple JWT",
            "PostgreSQL",
            "Celery",
            "Redis",
            "TailwindCSS",
        ],
        "quick_links": quick_links,
        "module_cards": module_cards,
        "swagger_url": reverse("swagger-ui"),
        "base_url": base_url,
        "current_year": timezone.now().year,
    }

    return render(request, "api/developer_portal.html", context)


class HealthCheckAPIView(APIView):

    @extend_schema(
        summary="Health Check",
        description="Returns the status of the API.",
        responses={200: HealthCheckSerializer},
        tags=['Core']
    )
    def get(self, request):
        data = {
            "status": "ok",
            "message": "Multi-Vendor E-commerce Backend is running.",
        }

        serializer = HealthCheckSerializer(instance=data)

        return Response(serializer.data)


class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get Current User",
        description="Returns the currently authenticated user's basic info.",
        responses={200: OpenApiResponse(response=dict, description="User info")},
        tags=['Core']
    )
    def get(self, request):
        return Response(
            {
                "id": str(request.user.id),
                "email": request.user.email,
            }
        )
