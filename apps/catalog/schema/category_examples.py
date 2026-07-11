from drf_spectacular.utils import OpenApiExample


CATEGORY_LIST_RESPONSE = OpenApiExample(
    name="Category List",
    summary="Example category list response",
    response_only=True,
    value=[
        {
            "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "name": "Phones",
            "slug": "phones",
            "parent": None,
            "is_active": True,
        },
        {
            "id": "3fa85f64-5717-4562-b3fc-2c963f66afa7",
            "name": "Laptops",
            "slug": "laptops",
            "parent": None,
            "is_active": True,
        },
    ],
)


CATEGORY_DETAIL_RESPONSE = OpenApiExample(
    name="Category Detail",
    summary="Example category detail response",
    response_only=True,
    value={
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "name": "Phones",
        "slug": "phones",
        "parent": None,
        "is_active": True,
    },
)
