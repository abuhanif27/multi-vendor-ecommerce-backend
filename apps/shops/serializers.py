from rest_framework import serializers

from apps.shops.models import Shop


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
