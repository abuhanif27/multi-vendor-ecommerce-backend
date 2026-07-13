from django.db import transaction
from django.db.models import F

from apps.shops.models import ProductImage


class ProductImageService:
    """
    Business logic for product image ordering.
    """

    # ==========================================================
    # Private Helpers
    # ==========================================================

    @staticmethod
    def _resolve_sort_order(
        *,
        requested_sort_order,
        current_image_count,
    ):
        """
        Resolve the final sort order.

        Examples
        --------
        Images = 3

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
    def _shift_down(
        *,
        product,
        from_sort_order,
    ):
        """
        Shift images down.

        Before

        1
        2
        3

        insert at 2

        After

        1
        3
        4
        """

        ProductImage.objects.filter(
            product=product,
            sort_order__gte=from_sort_order,
        ).update(
            sort_order=F("sort_order") + 1,
        )

    @staticmethod
    def _shift_up(
        *,
        product,
        from_sort_order,
    ):
        """
        Close the gap after deletion.

        Before

        1
        2
        3
        4

        delete 2

        After

        1
        2
        3
        """

        ProductImage.objects.filter(
            product=product,
            sort_order__gt=from_sort_order,
        ).update(
            sort_order=F("sort_order") - 1,
        )

    # ==========================================================
    # Public API
    # ==========================================================

    @staticmethod
    def insert(
        *,
        product,
        image,
        sort_order=None,
    ):
        """
        Insert a new image.
        """

        current_image_count = product.images.count()

        sort_order = ProductImageService._resolve_sort_order(
            requested_sort_order=sort_order,
            current_image_count=current_image_count,
        )

        with transaction.atomic():

            ProductImageService._shift_down(
                product=product,
                from_sort_order=sort_order,
            )

            return ProductImage.objects.create(
                product=product,
                image=image,
                sort_order=sort_order,
            )

    @staticmethod
    def delete(
        *,
        product_image,
    ):
        """
        Delete an image and close the ordering gap.
        """

        with transaction.atomic():

            deleted_sort_order = product_image.sort_order
            product = product_image.product

            product_image.delete()

            ProductImageService._shift_up(
                product=product,
                from_sort_order=deleted_sort_order,
            )

    @staticmethod
    def move(
        *,
        product_image,
        requested_sort_order,
    ):
        """
        Move an image to another position.
        """

        product = product_image.product

        current_image_count = product.images.count()

        new_sort_order = ProductImageService._resolve_sort_order(
            requested_sort_order=requested_sort_order,
            current_image_count=current_image_count,
        )

        old_sort_order = product_image.sort_order

        if old_sort_order == new_sort_order:
            return product_image

        with transaction.atomic():

            #
            # Moving DOWN
            #
            # 2 -> 5
            #

            if old_sort_order < new_sort_order:

                ProductImage.objects.filter(
                    product=product,
                    sort_order__gt=old_sort_order,
                    sort_order__lte=new_sort_order,
                ).update(
                    sort_order=F("sort_order") - 1,
                )

            #
            # Moving UP
            #
            # 5 -> 2
            #

            else:

                ProductImage.objects.filter(
                    product=product,
                    sort_order__gte=new_sort_order,
                    sort_order__lt=old_sort_order,
                ).update(
                    sort_order=F("sort_order") + 1,
                )

            product_image.sort_order = new_sort_order
            product_image.save(
                update_fields=[
                    "sort_order",
                ]
            )

        return product_image
