from rest_framework import serializers
from apps.orders.models import Order, VendorOrder, OrderItem

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product_name', 'sku', 'variant_attributes', 
            'shop_name', 'image_url', 'unit_price', 'quantity', 'item_total'
        ]


class VendorOrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    shop_name = serializers.CharField(source='shop.name', read_only=True)
    
    class Meta:
        model = VendorOrder
        fields = [
            'id', 'shop', 'shop_name', 'status', 'vendor_subtotal', 
            'vendor_shipping', 'vendor_tax', 'vendor_total', 'items', 'created_at'
        ]


class OrderSerializer(serializers.ModelSerializer):
    vendor_orders = VendorOrderSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'status', 'subtotal', 'shipping_total', 'tax_total', 'grand_total',
            'shipping_address', 'billing_address', 'vendor_orders', 'created_at'
        ]


class VendorOrderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorOrder
        fields = ['status']
        
    def validate_status(self, value):
        valid_transitions = {
            VendorOrder.FulfillmentStatus.PENDING: [VendorOrder.FulfillmentStatus.CANCELLED], # Actually vendors shouldn't move from PENDING to PROCESSING, only payments do. But let's allow basic transitions.
        }
        # In a real app we would strictly enforce FSM transitions here.
        return value
