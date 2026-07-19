from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated

from apps.common.mixins import ReadResponseMixin, ReadSerializerMixin
from apps.shops.models import VariantImage
from apps.shops.mixins import ProductLookupMixin
from apps.shops.permissions import IsVariantImageOwner
from apps.shops.serializers.variant_images import (
    VariantImageReadSerializer,
    VariantImageWriteSerializer,
)


class VariantLookupMixin(ProductLookupMixin):
    def get_variant(self):
        product = self.get_product()
        sku = self.kwargs["sku"]
        return get_object_or_404(product.variants.all(), sku=sku)


class VariantImageSerializerMixin(ReadSerializerMixin):
    read_serializer_class = VariantImageReadSerializer

    def get_serializer_class(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return VariantImageReadSerializer
        return VariantImageWriteSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if hasattr(self, "get_variant"):
            context["variant"] = self.get_variant()
        return context


class VariantImageQuerysetMixin:
    def get_queryset(self):
        return self.get_variant().images.all()


class VariantImagePermissionMixin:
    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [AllowAny()]
        return [IsAuthenticated(), IsVariantImageOwner()]


class VariantImageCreateAPIView(
    VariantLookupMixin,
    VariantImageSerializerMixin,
    VariantImageQuerysetMixin,
    VariantImagePermissionMixin,
    ReadResponseMixin,
    generics.CreateAPIView,
):
    queryset = VariantImage.objects.all()


class VariantImageDetailAPIView(
    VariantLookupMixin,
    VariantImageSerializerMixin,
    VariantImageQuerysetMixin,
    VariantImagePermissionMixin,
    ReadResponseMixin,
    generics.RetrieveUpdateDestroyAPIView,
):
    queryset = VariantImage.objects.all()
