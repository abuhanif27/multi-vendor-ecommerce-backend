from rest_framework import serializers

from apps.shops.models import Product
from apps.shops.serializers.product_images import ProductImageReadSerializer


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageReadSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "shop",
            "category",
            "name",
            "slug",
            "description",
            "status",
            "images",
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
