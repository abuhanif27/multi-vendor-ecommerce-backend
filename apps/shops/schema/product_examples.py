from drf_spectacular.utils import OpenApiExample


CREATE_PRODUCT_EXAMPLE = OpenApiExample(
    "Create Product",
    summary="Example request",
    request_only=True,
    value={
        "shop": "apple-store",
        "category": "phones",
        "name": "iPhone 16 Pro",
        "description": "Latest Apple flagship smartphone.",
        "price": "1499.00",
        "stock": 25,
        "status": "active",
    },
)


UPDATE_PRODUCT_EXAMPLE = OpenApiExample(
    "Update Product",
    summary="Partial update",
    request_only=True,
    value={
        "price": "1399.00",
        "stock": 40,
    },
)
