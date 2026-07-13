from rest_framework import serializers

from apps.shops.models import ProductImage
from apps.shops.services import ProductImageService


class ProductImageSerializer(serializers.ModelSerializer):
    sort_order = serializers.IntegerField(
        required=False,
        min_value=1,
    )

    is_primary = serializers.ReadOnlyField()

    class Meta:
        model = ProductImage

        fields = (
            "id",
            "image",
            "sort_order",
            "is_primary",
        )

        read_only_fields = (
            "id",
        )

    def validate(self, attrs):
        product = self.context.get("product")

        if product is None:
            raise AssertionError(
                "ProductImageSerializer requires "
                "'product' in serializer context."
            )

        if product.images.count() >= 5:
            raise serializers.ValidationError(
                {
                    "image": (
                        "A product can have a maximum "
                        "of 5 images."
                    )
                }
            )

        return attrs

    def create(self, validated_data):
        return ProductImageService.insert(
            product=self.context["product"],
            image=validated_data["image"],
            sort_order=validated_data.get(
                "sort_order"
            ),
        )


class ProductImageUpdateSerializer(
    serializers.Serializer,
):
    sort_order = serializers.IntegerField(
        min_value=1,
    )

    def update(
        self,
        instance,
        validated_data,
    ):
        return ProductImageService.move(
            product_image=instance,
            requested_sort_order=validated_data[
                "sort_order"
            ],
        )

    def create(self, validated_data):
        raise AssertionError(
            "ProductImageUpdateSerializer "
            "does not support create()."
        )
