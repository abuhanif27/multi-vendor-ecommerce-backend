import os
import sys

import django
from django.conf import settings
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.api.serializers import HealthCheckSerializer


def developer_portal(request):
    api_version = settings.SPECTACULAR_SETTINGS.get("VERSION", "v1")
    project_description = settings.SPECTACULAR_SETTINGS.get(
        "DESCRIPTION", "REST API developer portal.")
    page_description = (
        "Production-grade multi-vendor marketplace API with JWT authentication, Redis, Celery, "
        "Stripe, SSLCommerz, PostgreSQL, and OpenAPI documentation."
    )
    environment = os.environ.get(
        "DJANGO_ENV", "Development" if settings.DEBUG else "Production")
    database_engine = settings.DATABASES["default"]["ENGINE"].rsplit(
        ".", 1)[-1]
    database_name = settings.DATABASES["default"].get("NAME", "")
    base_url = request.build_absolute_uri("/").rstrip("/")
    canonical_url = request.build_absolute_uri(request.path)
    redis_url = getattr(settings, "REDIS_URL", "")

    platform_features = [
        "Multi-Vendor Marketplace",
        "JWT Authentication",
        "Email Verification",
        "Stripe Integration",
        "SSLCommerz Integration",
        "Event-Driven Architecture",
        "Service Layer Pattern",
        "RBAC",
        "OpenAPI Documentation",
        "PostgreSQL",
        "Redis",
        "Celery",
        "Comprehensive Test Suite",
    ]

    quick_links = [
        {"label": "Swagger UI", "url": reverse(
            "swagger-ui"), "style": "primary"},
        {"label": "ReDoc", "url": reverse("redoc"), "style": "secondary"},
        {"label": "OpenAPI Schema", "url": reverse(
            "schema"), "style": "secondary"},
        {"label": "Health Check", "url": reverse(
            "health-check-root"), "style": "secondary"},
        {"label": "Django Admin", "url": reverse(
            "admin:index"), "style": "secondary"},
        {"label": "GitHub Repository",
            "url": settings.PROJECT_REPOSITORY_URL, "style": "secondary"},
    ]

    module_cards = [
        {
            "name": "Authentication",
            "purpose": "Registers users, issues JWT credentials, and verifies email ownership.",
        },
        {
            "name": "Users",
            "purpose": "Provides authenticated profile context and account-facing user data.",
        },
        {
            "name": "Vendors",
            "purpose": "Supports vendor onboarding, approvals, and operational vendor administration.",
        },
        {
            "name": "Shops",
            "purpose": "Creates, lists, retrieves, and maintains vendor storefronts.",
        },
        {
            "name": "Categories",
            "purpose": "Organizes catalog data through browsable product categories.",
        },
        {
            "name": "Products",
            "purpose": "Publishes and manages marketplace product listings.",
        },
        {
            "name": "Inventory",
            "purpose": "Tracks stock levels and inventory movement across variants.",
        },
        {
            "name": "Cart",
            "purpose": "Maintains buyer carts, cart items, quantities, and cart totals.",
        },
        {
            "name": "Checkout",
            "purpose": "Validates cart state and prepares order creation from selected items.",
        },
        {
            "name": "Orders",
            "purpose": "Exposes buyer orders and vendor-specific order fulfillment views.",
        },
        {
            "name": "Payments",
            "purpose": "Initializes payments and receives asynchronous gateway webhooks.",
        },
        {
            "name": "Refunds",
            "purpose": "Represents refund records created from payment and return workflows.",
        },
        {
            "name": "Returns",
            "purpose": "Supports post-order return flows through order domain records.",
        },
        {
            "name": "Shipping",
            "purpose": "Tracks shipments, assigns couriers, and updates delivery status.",
        },
        {
            "name": "Reviews",
            "purpose": "Captures product and shop feedback, reports, and moderation status.",
        },
        {
            "name": "Notifications",
            "purpose": "Delivers and manages in-app notifications for authenticated users.",
        },
        {
            "name": "Promotions",
            "purpose": "Evaluates coupons, public promotions, and administrative promotion rules.",
        },
        {
            "name": "Analytics",
            "purpose": "Provides vendor dashboards and sales export workflows.",
        },
        {
            "name": "Administration",
            "purpose": "Moderates vendors, products, reviews, and platform promotions.",
        },
    ]

    context = {
        "project_title": settings.SPECTACULAR_SETTINGS.get("TITLE", "Marketplace API"),
        "project_description": project_description,
        "page_description": page_description,
        "api_version": api_version,
        "environment": environment,
        "django_version": django.get_version(),
        "python_version": sys.version.split()[0],
        "database_engine": database_engine,
        "database_name": database_name,
        "is_postgresql": "postgresql" in settings.DATABASES["default"]["ENGINE"],
        "redis_url": redis_url,
        "is_redis_configured": bool(redis_url),
        "jwt_authentication": "Enabled",
        "stripe_enabled": bool(settings.STRIPE_SECRET_KEY),
        "sslcommerz_enabled": bool(settings.SSLCOMMERZ_STORE_ID),
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
        "platform_features": platform_features,
        "quick_links": quick_links,
        "module_cards": module_cards,
        "swagger_url": reverse("swagger-ui"),
        "base_url": base_url,
        "canonical_url": canonical_url,
        "repository_url": settings.PROJECT_REPOSITORY_URL,
        "theme_color": "#020617",
        "site_name": settings.SPECTACULAR_SETTINGS.get(
            "TITLE", "Multi-Vendor Marketplace API"),
        "social_image_url": request.build_absolute_uri("/static/social-card.svg"),
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
        responses={200: OpenApiResponse(
            response=dict, description="User info")},
        tags=['Core']
    )
    def get(self, request):
        return Response(
            {
                "id": str(request.user.id),
                "email": request.user.email,
            }
        )
