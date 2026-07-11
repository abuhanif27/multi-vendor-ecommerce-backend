from drf_spectacular.utils import (
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)
from apps.shops.schema.shop_examples import (
    CREATE_SHOP_EXAMPLE,
    UPDATE_SHOP_EXAMPLE,
)

from apps.shops.serializers import ShopSerializer

SHOP_LIST_SCHEMA = extend_schema_view(
    get=extend_schema(
        tags=["Shops"],
        summary="List shops",
        description="""
Returns all approved shops.

This endpoint is public.

Supports:
- Pagination
""",
        responses={
            200: ShopSerializer,
        },
    ),
    post=extend_schema(
        tags=["Shops"],
        summary="Create shop",
        description="""
Creates a new shop for the authenticated vendor.

Authentication:
- Vendor only
""",
        request=ShopSerializer,
        responses={
            201: ShopSerializer,
            400: None,
            401: None,
            403: None,
        },
        examples=[
            CREATE_SHOP_EXAMPLE,
        ]
    ),
)

SHOP_DETAIL_SCHEMA = extend_schema_view(
    get=extend_schema(
        tags=["Shops"],
        summary="Retrieve Shop",
        description="""
Retrieve a single active Shop by its slug.

This endpoint is public.
""",
        responses={
            200: ShopSerializer,
            404: None,
        },
    ),
    patch=extend_schema(
        tags=["Shops"],
        summary="Update Shop",
        description="""
Partially update a Shop.

Requirements:
- Authenticated user
- Vendor role
- Shop owner
""",
        request=ShopSerializer,
        responses={
            200: ShopSerializer,
            400: None,
            401: None,
            403: None,
            404: None,
        },
        examples=[
            UPDATE_SHOP_EXAMPLE,
        ]
    ),
    put=extend_schema(
        exclude=True,
    ),
    delete=extend_schema(
        tags=["Shops"],
        summary="Delete Shop",
        description="""
Delete a Shop.

Requirements:
- Authenticated user
- Vendor role
- Shop owner
""",
        responses={
            204: None,
            401: None,
            403: None,
            404: None,
        },
    ),
)

MY_SHOPS_SCHEMA = extend_schema_view(
    get=extend_schema(
        tags=["Vendor"],
        summary="My shops",
        description="Returns all shops owned by the authenticated vendor.",
        responses={
            200: ShopSerializer,
            401: None,
            403: None,
        },
    ),
)
