from drf_spectacular.utils import OpenApiExample


CREATE_SHOP_EXAMPLE = OpenApiExample(
    "Create Shop",
    summary="Example shop creation",
    request_only=True,
    value={
        "name": "Apple Store",
    },
)


UPDATE_SHOP_EXAMPLE = OpenApiExample(
    "Rename Shop",
    summary="Partial update",
    request_only=True,
    value={
        "name": "Apple Official Store",
    },
)
