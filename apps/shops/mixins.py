from django.shortcuts import get_object_or_404

from apps.shops.models import Product


class ProductLookupMixin:
    """
    Resolve the parent product from the URL.
    """

    def get_product(self):
        if not hasattr(self, "_cached_product"):
            self._cached_product = get_object_or_404(
                Product.objects.select_related(
                    "shop",
                ),
                shop__slug=self.kwargs["shop_slug"],
                slug=self.kwargs["product_slug"],
            )

        return self._cached_product
