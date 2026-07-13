from apps.shops.services import ProductImageService
from apps.shops.models import ProductImage
from rest_framework import serializers

from django.db import transaction
from django.db.models import F
from apps.shops.models import (
    Shop,
    Product,
    ProductImage
)


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = (
            "id",
            "name",
            "slug",
            "status",
        )
        read_only_fields = (
            "id",
            "slug",
            "status",
        )


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            "id",
            "shop",
            "category",
            "name",
            "slug",
            "description",
            "price",
            "stock",
            "status",
        )

        read_only_fields = (
            "id",
            "slug",
            "status",
        )

    def validate_shop(self, shop):
        request = self.context.get("request")
        if request.user != shop.owner:
            raise serializers.ValidationError(
                "You do not have permission to add a product to this shop."
            )
        return shop

    def validate_category(self, category):
        if not category.is_active:
            raise serializers.ValidationError(
                "You cannot add a product to an inactive category."
            )
        return category


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
            sort_order=validated_data.get("sort_order"),
        )
