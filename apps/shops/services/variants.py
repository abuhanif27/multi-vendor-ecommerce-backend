from django.core.exceptions import ValidationError
from django.db import transaction

from apps.catalog.models import (
    CategoryAttributeValue,
)
from apps.catalog.services import (
    CategoryService,
)

from apps.shops.models import (
    Product,
    ProductVariant,
    VariantAttributeValue,
)


class VariantService:
    """
    Business logic for product variants.
    """

    @classmethod
    def create(cls):
        raise NotImplementedError

    @classmethod
    def update(cls):
        raise NotImplementedError

    @classmethod
    def delete(cls):
        raise NotImplementedError

    @classmethod
    def _validate_category(
        cls,
        product: Product,
        selected_values: list[CategoryAttributeValue],
    ) -> None:
        """
        Ensure every selected value belongs to one of the
        product category's available attributes, including
        inherited attributes.
        """

        allowed_attributes = CategoryService.get_attributes(
            product.category,
        )

        allowed_attribute_ids = {
            attribute.id
            for attribute in allowed_attributes
        }

        for value in selected_values:
            if value.category_attribute_id not in allowed_attribute_ids:
                raise ValidationError(
                    {
                        "attributes": (
                            f'"{value}" is not valid for '
                            f'category "{product.category}".'
                        )
                    }
                )

    @classmethod
    def _validate_unique_attributes(
        cls,
        selected_values: list[CategoryAttributeValue],
    ) -> None:
        """
        Ensure only one value is selected for each attribute.
        """

        seen_attribute_ids = set()

        for value in selected_values:
            attribute_id = value.category_attribute_id

            if attribute_id in seen_attribute_ids:
                raise ValidationError(
                    {
                        "attributes": (
                            f'Attribute "{value.category_attribute.name}" '
                            "can only have one selected value."
                        )
                    }
                )

            seen_attribute_ids.add(attribute_id)

    @classmethod
    def _validate_required_attributes(
        cls,
        product: Product,
        selected_values: list[CategoryAttributeValue],
    ) -> None:
        """
        Ensure all required attributes have a selected value.
        """

        available_attributes = CategoryService.get_attributes(
            product.category,
        )

        required_attribute_ids = {
            attribute.id
            for attribute in available_attributes
            if attribute.is_required
        }

        selected_attribute_ids = {
            value.category_attribute_id
            for value in selected_values
        }

        missing_attribute_ids = (
            required_attribute_ids
            - selected_attribute_ids
        )

        if not missing_attribute_ids:
            return

        missing_attribute_names = [
            attribute.name
            for attribute in available_attributes
            if attribute.id in missing_attribute_ids
        ]

        raise ValidationError(
            {
                "attributes": (
                    "Missing required attributes: "
                    + ", ".join(missing_attribute_names)
                )
            }
        )

    @classmethod
    def _validate_duplicate_variant(
        cls,
        product: Product,
        selected_values: list[CategoryAttributeValue],
    ) -> None:
        """
        Ensure the product does not already contain
        a variant with the same attribute combination.
        """

        selected_value_ids = {
            value.id
            for value in selected_values
        }

        variants = (
            ProductVariant.objects
            .filter(product=product)
            .prefetch_related(
                "attribute_values__category_attribute_value",
            )
        )

        for variant in variants:
            existing_value_ids = {
                item.category_attribute_value_id
                for item in variant.attribute_values.all()
            }

            if selected_value_ids == existing_value_ids:
                raise ValidationError(
                    {
                        "attributes": (
                            "A variant with the selected "
                            "attribute combination already exists."
                        )
                    }
                )

    @classmethod
    def create(
        cls,
        *,
        product: Product,
        sku: str,
        price,
        stock: int,
        barcode: str = "",
        status,
        selected_values: list[CategoryAttributeValue],
    ) -> ProductVariant:
        with transaction.atomic():

            cls._validate_category(
                product=product,
                selected_values=selected_values,
            )

            cls._validate_unique_attributes(
                selected_values=selected_values,
            )

            cls._validate_required_attributes(
                product=product,
                selected_values=selected_values,
            )

            cls._validate_duplicate_variant(
                product=product,
                selected_values=selected_values,
            )

            variant = ProductVariant.objects.create(
                product=product,
                sku=sku,
                price=price,
                stock=stock,
                barcode=barcode,
                status=status,
            )

            VariantAttributeValue.objects.bulk_create(
                [
                    VariantAttributeValue(
                        variant=variant,
                        category_attribute_value=value,
                    )
                    for value in selected_values
                ]
            )

            return variant

    @classmethod
    def update(
        cls,
        *,
        variant: ProductVariant,
        sku: str,
        price,
        stock: int,
        barcode: str = "",
        status,
        selected_values: list[CategoryAttributeValue],
    ) -> ProductVariant:
        raise NotImplementedError

    @classmethod
    def delete(
        cls,
        *,
        variant: ProductVariant,
    ) -> None:
        raise NotImplementedError
