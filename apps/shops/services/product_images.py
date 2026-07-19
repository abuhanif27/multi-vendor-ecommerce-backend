from django.db import transaction
from django.db.models import F

from apps.shops.models import Product, ProductImage


class ProductImageService:
    """
    Business logic for product images.
    """

    @classmethod
    def create(
        cls,
        *,
        product: Product,
        image,
        alt_text: str = "",
    ) -> ProductImage:
        """
        Create a product image. 
        If it's the first image, it becomes primary automatically.
        Appended at the end of the display order.
        """
        with transaction.atomic():
            current_image_count = product.images.count()
            
            is_primary = current_image_count == 0
            display_order = current_image_count + 1

            return ProductImage.objects.create(
                product=product,
                image=image,
                alt_text=alt_text,
                display_order=display_order,
                is_primary=is_primary,
            )

    @classmethod
    def update(
        cls,
        *,
        product_image: ProductImage,
        alt_text: str,
    ) -> ProductImage:
        """
        Update a product image.
        """
        product_image.alt_text = alt_text
        product_image.save(update_fields=["alt_text", "updated_at"])
        return product_image

    @classmethod
    def delete(
        cls,
        *,
        product_image: ProductImage,
    ) -> None:
        """
        Delete a product image, close the display order gap,
        and reassign primary status if necessary.
        """
        with transaction.atomic():
            product = product_image.product
            deleted_display_order = product_image.display_order
            was_primary = product_image.is_primary

            product_image.delete()

            # Shift up the remaining images to close the gap
            product.images.filter(
                display_order__gt=deleted_display_order
            ).update(
                display_order=F("display_order") - 1
            )

            # Reassign primary if the deleted one was primary
            if was_primary:
                new_primary = product.images.order_by("display_order").first()
                if new_primary:
                    new_primary.is_primary = True
                    new_primary.save(update_fields=["is_primary", "updated_at"])

    @classmethod
    def set_primary(
        cls,
        *,
        product_image: ProductImage,
    ) -> None:
        """
        Set the given image as primary, and remove primary status from others.
        """
        with transaction.atomic():
            if product_image.is_primary:
                return

            product = product_image.product
            
            # Remove primary from all
            product.images.filter(is_primary=True).update(is_primary=False)
            
            # Set as primary
            product_image.is_primary = True
            product_image.save(update_fields=["is_primary", "updated_at"])

    @classmethod
    def reorder(
        cls,
        *,
        product: Product,
        image_ids: list[str],
    ) -> None:
        """
        Update the display order of all images for the product.
        image_ids should be a list of UUIDs in the desired order.
        """
        with transaction.atomic():
            # Validate that the provided IDs match the product's images exactly
            existing_images = list(product.images.all())
            existing_ids = {str(img.id) for img in existing_images}
            provided_ids = {str(img_id) for img_id in image_ids}
            
            if existing_ids != provided_ids:
                raise ValueError("Provided image IDs do not match the product's images.")
            
            # Bulk update display_order
            images_to_update = []
            for order, image_id in enumerate(image_ids, start=1):
                for img in existing_images:
                    if str(img.id) == str(image_id):
                        if img.display_order != order:
                            img.display_order = order
                            images_to_update.append(img)
                        break
            
            if images_to_update:
                ProductImage.objects.bulk_update(images_to_update, ["display_order"])
