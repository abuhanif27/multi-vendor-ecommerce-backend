from rest_framework import generics

from apps.common.permissions import IsVendor
from apps.common.views import UpdateDestroyAPIView

from apps.shops.mixins import (
    ProductLookupMixin,
    ProductImageLookupMixin,
)

from apps.shops.serializers import (
    ProductImageSerializer,
    ProductImageUpdateSerializer,
)

from apps.shops.services import ProductImageService


class ProductImageCreateAPIView(
    ProductLookupMixin,
    generics.CreateAPIView,
):
    serializer_class = ProductImageSerializer
    permission_classes = [IsVendor]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["product"] = self.get_product()
        return context


class ProductImageDetailAPIView(
    ProductImageLookupMixin,
    UpdateDestroyAPIView,
):
    serializer_class = ProductImageUpdateSerializer
    permission_classes = [IsVendor]

    def perform_destroy(self, instance):
        ProductImageService.delete(
            product_image=instance,
        )
