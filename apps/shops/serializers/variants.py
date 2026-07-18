from rest_framework import serializers

from apps.catalog.models import CategoryAttributeValue
from apps.shops.models import (
    ProductVariant,
    VariantAttributeValue,
)
from apps.shops.services import VariantService


class VariantAttributeValueSerializer(
    serializers.ModelSerializer,
):
    attribute = serializers.CharField(
        source=(
            "category_attribute_value."
            "category_attribute.name"
        ),
        read_only=True,
    )

    value = serializers.CharField(
        source="category_attribute_value.value",
        read_only=True,
    )

    class Meta:
        model = VariantAttributeValue

        fields = (
            "attribute",
            "value",
        )


class VariantReadSerializer(
    serializers.ModelSerializer,
):
    attributes = VariantAttributeValueSerializer(
        source="attribute_values",
        many=True,
        read_only=True,
    )

    class Meta:
        model = ProductVariant

        fields = (
            "id",
            "sku",
            "price",
            "stock",
            "barcode",
            "status",
            "attributes",
        )

        read_only_fields = fields


class VariantWriteSerializer(
    serializers.ModelSerializer,
):
    selected_values = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=CategoryAttributeValue.objects.all(),
        write_only=True,
        required=True,
    )

    class Meta:
        model = ProductVariant

        fields = (
            "sku",
            "price",
            "stock",
            "barcode",
            "status",
            "selected_values",
        )

    def validate(self, attrs):
        """
        Ensure the serializer receives the product
        from the view through serializer context.
        """

        if "product" not in self.context:
            raise AssertionError(
                "VariantWriteSerializer requires "
                "'product' in serializer context."
            )

        return attrs

    def create(self, validated_data):
        """
        Delegate variant creation to the service layer.
        """

        return VariantService.create(
            product=self.context["product"],
            **validated_data,
        )

    def update(
        self,
        instance,
        validated_data,
    ):
        """
        Delegate variant update to the service layer.
        """

        return VariantService.update(
            variant=instance,
            **validated_data,
        )
