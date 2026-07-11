from drf_spectacular.utils import (
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)

from apps.shops.serializers import ProductSerializer
from apps.shops.docs.product_examples import (
    CREATE_PRODUCT_EXAMPLE,
    UPDATE_PRODUCT_EXAMPLE,
)


PRODUCT_LIST_SCHEMA = extend_schema_view(
    get=extend_schema(
        tags=["Products"],
        summary="List products",
        description="""
Returns active products from approved shops.

Features:

- Pagination
- Category filtering
- Shop filtering
- Price filtering
- Search
- Ordering

Public endpoint.
""",
        parameters=[
            OpenApiParameter(
                name="category",
                type=str,
                description="Category slug.",
            ),
            OpenApiParameter(
                name="shop",
                type=str,
                description="Shop slug.",
            ),
            OpenApiParameter(
                name="min_price",
                type=float,
                description="Minimum product price.",
            ),
            OpenApiParameter(
                name="max_price",
                type=float,
                description="Maximum product price.",
            ),
            OpenApiParameter(
                name="search",
                type=str,
                description="Search by product name, description, shop name or category name.",
            ),
            OpenApiParameter(
                name="ordering",
                type=str,
                description="Available values: price, -price, name, created_at, -created_at.",
            ),
        ],
        responses={
            200: ProductSerializer,
        },
    ),
    post=extend_schema(
        tags=["Products"],
        summary="Create product",
        description="""
Creates a new product for the authenticated vendor.

Requirements:

- Authenticated user
- Vendor role
""",
        request=ProductSerializer,
        responses={
            201: ProductSerializer,
            400: None,
            401: None,
            403: None,
        },
        examples=[
            CREATE_PRODUCT_EXAMPLE,
        ]
    ),
)
PRODUCT_DETAIL_SCHEMA = extend_schema_view(
    get=extend_schema(
        tags=["Products"],
        summary="Retrieve product",
        description="""
Retrieve a single active product by its slug.

This endpoint is public.
""",
        responses={
            200: ProductSerializer,
            404: None,
        },
    ),
    patch=extend_schema(
        tags=["Products"],
        summary="Update product",
        description="""
Partially update a product.

Requirements:
- Authenticated user
- Vendor role
- Product owner
""",
        request=ProductSerializer,
        responses={
            200: ProductSerializer,
            400: None,
            401: None,
            403: None,
            404: None,
        },
        examples=[
            UPDATE_PRODUCT_EXAMPLE,
        ]
    ),
    put=extend_schema(
        exclude=True,
    ),
    delete=extend_schema(
        tags=["Products"],
        summary="Delete product",
        description="""
Delete a product.

Requirements:
- Authenticated user
- Vendor role
- Product owner
""",
        responses={
            204: None,
            401: None,
            403: None,
            404: None,
        },
    ),
)
MY_PRODUCTS_SCHEMA = extend_schema_view(
    get=extend_schema(
        tags=["Vendor"],
        summary="My products",
        description="Returns all products owned by the authenticated vendor.",
        responses={
            200: ProductSerializer,
            401: None,
            403: None,
        },
    ),
)
