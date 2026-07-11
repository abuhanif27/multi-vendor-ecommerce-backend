from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.catalog.serializers import CategorySerializer
from apps.catalog.schema.category_examples import (
    CATEGORY_LIST_RESPONSE,
    CATEGORY_DETAIL_RESPONSE,
)

CATEGORY_LIST_SCHEMA = extend_schema_view(
    get=extend_schema(
        tags=["Categories"],
        summary="List categories",
        description="""
Returns all active categories.

Public endpoint.
""",
        responses={
            200: CategorySerializer,
        },
        examples=[
            CATEGORY_LIST_RESPONSE,
        ],
    ),
)

CATEGORY_DETAIL_SCHEMA = extend_schema_view(
    get=extend_schema(
        tags=["Categories"],
        summary="Retrieve category",
        description="""
Retrieve a category by its slug.

Public endpoint.
""",
        responses={
            200: CategorySerializer,
            404: None,
        },
        examples=[
            CATEGORY_DETAIL_RESPONSE,
        ],
    ),
)
