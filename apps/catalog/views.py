from rest_framework import generics

from apps.catalog.models import Category
from apps.catalog.serializers import CategorySerializer


class CategoryListAPIView(generics.ListAPIView):
    serializer_class = CategorySerializer

    def get_queryset(self):
        return (
            Category.objects
            .select_related("parent")
            .filter(is_active=True)
        )


class CategoryDetailAPIView(generics.RetrieveAPIView):
    serializer_class = CategorySerializer
    lookup_field = "slug"

    def get_queryset(self):
        return (
            Category.objects
            .select_related("parent")
            .filter(is_active=True)
        )
