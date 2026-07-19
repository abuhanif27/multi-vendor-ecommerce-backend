from rest_framework import serializers
from apps.inventory.models import Inventory

class InventoryReadSerializer(serializers.ModelSerializer):
    available_quantity = serializers.SerializerMethodField()

    class Meta:
        model = Inventory
        fields = (
            "id",
            "quantity_on_hand",
            "quantity_reserved",
            "available_quantity",
            "low_stock_threshold",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_available_quantity(self, obj):
        return obj.quantity_on_hand - obj.quantity_reserved
