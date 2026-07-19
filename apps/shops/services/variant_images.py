from django.db import transaction
from django.db.models import F

from apps.shops.models import VariantImage


class VariantImageService:
    @staticmethod
    @transaction.atomic
    def create(*, variant, image, alt_text=""):
        """
        Creates a new VariantImage.
        If this is the first image for the variant, it becomes the primary image.
        """
        existing_images_count = variant.images.count()
        is_primary = existing_images_count == 0
        display_order = existing_images_count + 1

        variant_image = VariantImage(
            variant=variant,
            image=image,
            alt_text=alt_text,
            is_primary=is_primary,
            display_order=display_order,
        )
        variant_image.save()
        return variant_image

    @staticmethod
    @transaction.atomic
    def update(*, variant_image, alt_text=None):
        """
        Updates an existing VariantImage's details.
        """
        if alt_text is not None:
            variant_image.alt_text = alt_text
        variant_image.save()
        return variant_image

    @staticmethod
    @transaction.atomic
    def delete(*, variant_image):
        """
        Deletes a VariantImage and re-orders the remaining images.
        If the primary image is deleted, assigns primary to the next available.
        """
        variant = variant_image.variant
        was_primary = variant_image.is_primary
        deleted_order = variant_image.display_order

        variant_image.delete()

        # Shift display order down for all subsequent images
        variant.images.filter(display_order__gt=deleted_order).update(
            display_order=F("display_order") - 1
        )

        # Reassign primary if needed
        if was_primary:
            first_image = variant.images.order_by("display_order").first()
            if first_image:
                first_image.is_primary = True
                first_image.save(update_fields=["is_primary"])

    @staticmethod
    @transaction.atomic
    def set_primary(*, variant_image):
        """
        Sets the given image as primary and removes primary status from others.
        """
        variant = variant_image.variant

        variant.images.filter(is_primary=True).update(is_primary=False)
        
        variant_image.is_primary = True
        variant_image.save(update_fields=["is_primary"])
        return variant_image

    @staticmethod
    @transaction.atomic
    def reorder(*, variant, image_ids):
        """
        Reorders the images based on the provided list of IDs.
        """
        for index, image_id in enumerate(image_ids, start=1):
            VariantImage.objects.filter(id=image_id, variant=variant).update(
                display_order=index
            )
