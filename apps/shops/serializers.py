from rest_framework import serializers

from apps.shops.models import Shop, Product


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
