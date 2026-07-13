from django.db import transaction
from django.db.models import F

from apps.shops.models import ProductImage


class ProductImageService:
    @staticmethod
    def _resolve_sort_order(
        *,
        requested_sort_order,
        current_image_count,
    ):
        """
        Normalize the requested sort order.

        Examples:
            Images: 3

            None -> 4
            1    -> 1
            2    -> 2
            3    -> 3
            4    -> 4
            999  -> 4
        """

        if requested_sort_order is None:
            return current_image_count + 1

        return min(
            requested_sort_order,
            current_image_count + 1,
        )

    @staticmethod
    def insert(
        *,
        product,
        image,
        sort_order=None,
    ):
        current_image_count = product.images.count()

        sort_order = ProductImageService._resolve_sort_order(
            requested_sort_order=sort_order,
            current_image_count=current_image_count,
        )

        with transaction.atomic():

            ProductImage.objects.filter(
                product=product,
                sort_order__gte=sort_order,
            ).update(
                sort_order=F("sort_order") + 1,
            )

            return ProductImage.objects.create(
                product=product,
                image=image,
                sort_order=sort_order,
            )
