from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated

from apps.common.mixins import ReadResponseMixin, ReadSerializerMixin
from apps.shops.models import ProductImage
from apps.shops.mixins import ProductLookupMixin
from apps.shops.permissions import IsProductOwner, IsProductImageOwner

from apps.shops.serializers.product_images import (
    ProductImageReadSerializer,
    ProductImageWriteSerializer,
)
from apps.shops.services.product_images import ProductImageService


class ProductImageSerializerMixin(ReadSerializerMixin):
    read_serializer_class = ProductImageReadSerializer

    def get_serializer_class(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return ProductImageReadSerializer
        return ProductImageWriteSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["product"] = self.get_product()
        return context


class ProductImageQuerysetMixin:
    def get_queryset(self):
        return self.get_product().images.all()


class ProductImagePermissionMixin:
    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [AllowAny()]
        
        if self.request.method == "POST":
            return [IsProductOwner()]
            
        return [
            IsAuthenticated(),
            IsProductImageOwner(),
        ]


class ProductImageCreateAPIView(
    ProductLookupMixin,
    ProductImageSerializerMixin,
    ProductImageQuerysetMixin,
    ProductImagePermissionMixin,
    ReadResponseMixin,
    generics.CreateAPIView,
):
    queryset = ProductImage.objects.all()


class ProductImageDetailAPIView(
    ProductLookupMixin,
    ProductImageSerializerMixin,
    ProductImageQuerysetMixin,
    ProductImagePermissionMixin,
    ReadResponseMixin,
    generics.RetrieveUpdateDestroyAPIView,
):
    queryset = ProductImage.objects.all()

    def perform_destroy(self, instance):
        ProductImageService.delete(product_image=instance)
