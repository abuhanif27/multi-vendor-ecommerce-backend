from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
)

from apps.shops.models import (
    Product,
    ProductVariant,
    VariantAttributeValue,
)
from apps.shops.serializers import (
    VariantReadSerializer,
    VariantWriteSerializer,
)
from apps.common.mixins import (
    ReadResponseMixin,
    ReadSerializerMixin,
)
from apps.shops.permissions import (
    IsVariantOwner,
    IsProductOwner,
)
from apps.shops.mixins import ProductLookupMixin


class VariantSerializerMixin(ReadSerializerMixin):
    """
    Configure serializers for variant APIs.
    """
    read_serializer_class = VariantReadSerializer

    def get_serializer_class(self):
        if self.request.method in (
            "GET",
            "HEAD",
            "OPTIONS",
        ):
            return VariantReadSerializer

        return VariantWriteSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["product"] = self.get_product()
        return context


class VariantQuerysetMixin:
    """
    Provide an optimized queryset for product variants.
    """

    def get_queryset(self):
        return (
            self.get_product()
            .variants
            .select_related("inventory")
            .prefetch_related(
                Prefetch(
                    "attribute_values",
                    queryset=VariantAttributeValue.objects.select_related(
                        "category_attribute_value",
                        "category_attribute_value__category_attribute",
                    ),
                ),
                "images",
                "product__images",
            )
        )


class VariantPermissionMixin:
    """
    Configure permissions for variant APIs.
    """

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [AllowAny()]

        if self.request.method == "POST":
            return [IsProductOwner()]

        return [
            IsAuthenticated(),
            IsVariantOwner(),
        ]


class ProductVariantListCreateAPIView(
    ProductLookupMixin,
    VariantSerializerMixin,
    VariantQuerysetMixin,
    VariantPermissionMixin,
    ReadResponseMixin,
    generics.ListCreateAPIView,
):
    """
    List and create product variants.
    """
    queryset = ProductVariant.objects.all()


class ProductVariantDetailAPIView(
    ProductLookupMixin,
    VariantSerializerMixin,
    VariantQuerysetMixin,
    VariantPermissionMixin,
    ReadResponseMixin,
    generics.RetrieveUpdateDestroyAPIView,
):
    """
    Retrieve, update, and delete a product variant.
    """
    queryset = ProductVariant.objects.all()
    lookup_field = "sku"
    lookup_url_kwarg = "sku"
