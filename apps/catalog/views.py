from rest_framework import generics

from apps.catalog.models import Category
from apps.catalog.serializers import CategorySerializer
from apps.common.pagination import DefaultPagination
from apps.catalog.schema.categories import (
    CATEGORY_LIST_SCHEMA,
    CATEGORY_DETAIL_SCHEMA,
)


@CATEGORY_LIST_SCHEMA
class CategoryListAPIView(generics.ListAPIView):
    serializer_class = CategorySerializer
    pagination_class = DefaultPagination

    def get_queryset(self):
        return (
            Category.objects
            .select_related("parent")
            .filter(is_active=True)
        )


@CATEGORY_DETAIL_SCHEMA
class CategoryDetailAPIView(generics.RetrieveAPIView):
    serializer_class = CategorySerializer
    lookup_field = "slug"

    def get_queryset(self):
        return (
            Category.objects
            .select_related("parent")
            .filter(is_active=True)
        )
