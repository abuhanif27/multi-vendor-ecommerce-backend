from django.shortcuts import get_object_or_404

from rest_framework import generics

from apps.shops.models import Product, ProductImage


class ProductLookupMixin:
    """
    Provides cached product lookup.
    """

    def get_product(self):
        if not hasattr(self, "_cached_product"):
            self._cached_product = get_object_or_404(
                Product.objects.select_related(
                    "shop",
                ),
                slug=self.kwargs["product_slug"],
                shop__owner=self.request.user,
            )

        return self._cached_product


class ProductImageLookupMixin(ProductLookupMixin):
    """
    Provides cached product image lookup.
    """

    def get_product_image(self):
        if not hasattr(self, "_cached_product_image"):

            self._cached_product_image = get_object_or_404(
                ProductImage.objects.select_related(
                    "product",
                    "product__shop",
                ),
                id=self.kwargs["image_id"],
                product=self.get_product(),
            )

        return self._cached_product_image
