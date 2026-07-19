from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from rest_framework import generics

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
)


class ProductLookupMixin:
    """
    Resolve the parent product from the URL.
    """

    def get_product(self):
        if not hasattr(self, "_product"):
            self._product = get_object_or_404(
                Product,
                shop__slug=self.kwargs["shop_slug"],
                slug=self.kwargs["product_slug"],
            )

        return self._product


class ReadSerializerMixin:
    read_serializer_class = None

    def get_read_serializer(self, instance):
        if self.read_serializer_class is None:
            raise NotImplementedError(
                "read_serializer_class must be defined."
            )

        return self.read_serializer_class(
            instance,
            context=self.get_serializer_context(),
        )


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
            .prefetch_related(
                Prefetch(
                    "attribute_values",
                    queryset=VariantAttributeValue.objects.select_related(
                        "category_attribute_value",
                        "category_attribute_value__category_attribute",
                    ),
                )
            )
        )


class ProductVariantListCreateAPIView(
    ProductLookupMixin,
    VariantSerializerMixin,
    VariantQuerysetMixin,
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
    ReadResponseMixin,
    generics.RetrieveUpdateDestroyAPIView,
):
    """
    Retrieve, update, and delete a product variant.
    """
    queryset = ProductVariant.objects.all()
    lookup_field = "sku"
    lookup_url_kwarg = "sku"
