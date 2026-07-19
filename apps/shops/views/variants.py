from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from rest_framework import (
    generics,
    status,
)
from rest_framework.response import Response

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


class VariantSerializerMixin:
    """
    Configure serializers for variant APIs.
    """

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

    def get_read_serializer(
        self,
        instance,
    ):
        return VariantReadSerializer(
            instance,
            context=self.get_serializer_context(),
        )


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
    generics.ListCreateAPIView,
):
    """
    List and create product variants.
    """
    queryset = ProductVariant.objects.all()

    def create(
        self,
        request,
        *args,
        **kwargs,
    ):
        serializer = self.get_serializer(
            data=request.data,
        )
        serializer.is_valid(
            raise_exception=True,
        )

        instance = serializer.save()

        read_serializer = self.get_read_serializer(
            instance,
        )

        headers = self.get_success_headers(
            read_serializer.data,
        )

        return Response(
            read_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )


class ProductVariantDetailAPIView(
    ProductLookupMixin,
    VariantSerializerMixin,
    VariantQuerysetMixin,
    generics.RetrieveUpdateDestroyAPIView,
):
    """
    Retrieve, update, and delete a product variant.
    """
    queryset = ProductVariant.objects.all()
    lookup_field = "sku"
    lookup_url_kwarg = "sku"

    def update(
        self,
        request,
        *args,
        **kwargs,
    ):
        partial = kwargs.pop(
            "partial",
            False,
        )

        instance = self.get_object()

        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        instance = serializer.save()

        return Response(
            self.get_read_serializer(instance).data,
        )
