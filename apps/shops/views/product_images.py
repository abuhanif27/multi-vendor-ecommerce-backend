from django.shortcuts import get_object_or_404
from rest_framework import generics
from apps.shops.permissions import IsVendor
from apps.shops.serializers import ProductImageSerializer
from apps.shops.models import Product


class ProductImageCreateAPIView(generics.CreateAPIView):
    serializer_class = ProductImageSerializer
    permission_classes = [IsVendor]

    def get_product(self):
        if not hasattr(self, "_cached_product"):
            self._cached_product = get_object_or_404(
                Product.objects.select_related("shop"),
                slug=self.kwargs["product_slug"],
                shop__owner=self.request.user,
            )

        return self._cached_product

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["product"] = self.get_product()
        return context
