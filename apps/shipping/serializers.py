from rest_framework import serializers
from apps.shipping.models import Courier, Shipment, ShipmentTrackingEvent

class CourierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Courier
        fields = ['id', 'name', 'tracking_url_template']

class ShipmentTrackingEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShipmentTrackingEvent
        fields = ['status', 'location', 'description', 'created_at']

class ShipmentReadSerializer(serializers.ModelSerializer):
    courier = CourierSerializer(read_only=True)
    tracking_events = ShipmentTrackingEventSerializer(many=True, read_only=True)
    
    class Meta:
        model = Shipment
        fields = [
            'id', 'vendor_order_id', 'status', 'courier', 
            'tracking_number', 'tracking_url', 'shipping_address_snapshot',
            'estimated_delivery_date', 'actual_delivery_date', 'tracking_events',
            'created_at', 'updated_at'
        ]

class ShipmentCourierAssignSerializer(serializers.Serializer):
    courier_id = serializers.UUIDField()
    tracking_number = serializers.CharField(max_length=100)

class ShipmentStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Shipment.ShipmentStatus.choices)
    location = serializers.CharField(max_length=255, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
