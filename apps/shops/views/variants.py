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


class ProductVariantListCreateAPIView(
    ProductLookupMixin,
    generics.ListCreateAPIView,
):
    queryset = ProductVariant.objects.all()

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


class ProductVariantDetailAPIView(
    ProductLookupMixin,
    generics.RetrieveUpdateDestroyAPIView,
):
    queryset = ProductVariant.objects.all()

    def get_object(self):
        return get_object_or_404(
            ProductVariant.objects.prefetch_related(
                Prefetch(
                    "attribute_values",
                    queryset=VariantAttributeValue.objects.select_related(
                        "category_attribute_value",
                        "category_attribute_value__category_attribute",
                    ),
                )
            ),
            product=self.get_product(),
            sku=self.kwargs["sku"],
        )

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
