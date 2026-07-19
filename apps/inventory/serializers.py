from rest_framework import serializers
from apps.inventory.models import Inventory, InventoryTransaction

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


class InventoryActionSerializer(serializers.Serializer):
    ACTION_CHOICES = (
        ("increase", "Increase"),
        ("decrease", "Decrease"),
        ("adjust", "Adjust"),
    )
    action = serializers.ChoiceField(choices=ACTION_CHOICES)
    quantity = serializers.IntegerField(min_value=0)
    note = serializers.CharField(required=False, allow_blank=True, max_length=1000)
    reference = serializers.CharField(required=False, allow_blank=True, max_length=255)

    def validate(self, attrs):
        if attrs["action"] in ["increase", "decrease"] and attrs["quantity"] < 1:
            raise serializers.ValidationError({"quantity": "Quantity must be at least 1 for increase/decrease."})
        return attrs


class InventoryTransactionSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()

    class Meta:
        model = InventoryTransaction
        fields = (
            "id",
            "transaction_type",
            "quantity",
            "note",
            "reference",
            "created_by",
            "created_at",
        )
        read_only_fields = fields
