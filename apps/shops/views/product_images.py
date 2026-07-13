from rest_framework import generics

from apps.shops.permissions import IsVendor
from apps.shops.serializers import ProductImageSerializer, ProductImageMoveSerializer
from apps.shops.mixins import ProductLookupMixin, ProductImageLookupMixin
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


class ProductImageMoveAPIView(
    ProductImageLookupMixin,
    generics.UpdateAPIView,
):
    serializer_class = ProductImageMoveSerializer
    permission_classes = [IsVendor]

    http_method_names = [
        "patch",
    ]

    def get_object(self):
        return self.get_product_image()


class ProductImageDeleteAPIView(
    ProductImageLookupMixin,
    generics.DestroyAPIView,
):
    permission_classes = [IsVendor]

    def get_object(self):
        return self.get_product_image()

    def perform_destroy(
        self,
        instance,
    ):
        ProductImageService.delete(
            product_image=instance,
        )
