from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.orders.models import VendorOrder
from apps.shipping.models import Shipment, ShipmentTrackingEvent
from apps.shipping.couriers.manual import ManualCourierStrategy

class ShippingService:
    """
    Manages the physical logistics FSM and append-only tracking events.
    """

    # Define the strict Finite State Machine transitions
    # Format: {CURRENT_STATE: [ALLOWED_NEXT_STATES]}
    ALLOWED_TRANSITIONS = {
        Shipment.ShipmentStatus.PENDING: [
            Shipment.ShipmentStatus.READY_FOR_PICKUP,
            Shipment.ShipmentStatus.SHIPPED,
            Shipment.ShipmentStatus.FAILED_DELIVERY # E.g., user cancelled before it shipped
        ],
        Shipment.ShipmentStatus.READY_FOR_PICKUP: [
            Shipment.ShipmentStatus.SHIPPED,
            Shipment.ShipmentStatus.FAILED_DELIVERY
        ],
        Shipment.ShipmentStatus.SHIPPED: [
            Shipment.ShipmentStatus.OUT_FOR_DELIVERY,
            Shipment.ShipmentStatus.FAILED_DELIVERY
        ],
        Shipment.ShipmentStatus.OUT_FOR_DELIVERY: [
            Shipment.ShipmentStatus.DELIVERED,
            Shipment.ShipmentStatus.FAILED_DELIVERY
        ],
        Shipment.ShipmentStatus.FAILED_DELIVERY: [
            Shipment.ShipmentStatus.RETURNED
        ],
        Shipment.ShipmentStatus.DELIVERED: [], # Terminal state
        Shipment.ShipmentStatus.RETURNED: []   # Terminal state
    }

    @staticmethod
    def _create_tracking_event(shipment, status, location="", description=""):
        """
        Private helper to enforce append-only event creation whenever status changes.
        """
        ShipmentTrackingEvent.objects.create(
            shipment=shipment,
            status=status,
            location=location,
            description=description
        )

    @staticmethod
    @transaction.atomic
    def initialize_shipment(vendor_order_id):
        """
        Creates the initial PENDING shipment. Called by OrderService when Order is PROCESSING.
        """
        vendor_order = VendorOrder.objects.select_for_update().get(id=vendor_order_id)
        
        # Guard against duplicate shipment creation
        if vendor_order.shipments.exists():
            return vendor_order.shipments.first()
            
        shipment = Shipment.objects.create(
            vendor_order=vendor_order,
            status=Shipment.ShipmentStatus.PENDING,
            shipping_address_snapshot=vendor_order.order.shipping_address
        )
        
        ShippingService._create_tracking_event(
            shipment=shipment, 
            status=Shipment.ShipmentStatus.PENDING,
            description="Shipment created and pending fulfillment."
        )
        return shipment

    @staticmethod
    @transaction.atomic
    def update_shipment_status(shipment_id, new_status, location="", description=""):
        """
        Advances the FSM. Validates transitions and logs tracking events.
        """
        shipment = Shipment.objects.select_for_update().get(id=shipment_id)
        
        current_status = shipment.status
        if new_status not in ShippingService.ALLOWED_TRANSITIONS.get(current_status, []):
            raise ValidationError(
                f"Invalid transition from {current_status} to {new_status}."
            )
            
        shipment.status = new_status
        if new_status == Shipment.ShipmentStatus.DELIVERED:
            shipment.actual_delivery_date = timezone.now()
            
        shipment.save(update_fields=['status', 'actual_delivery_date'])
        
        ShippingService._create_tracking_event(
            shipment=shipment, 
            status=new_status,
            location=location,
            description=description
        )
        
        # Fire Business Hooks
        if new_status == Shipment.ShipmentStatus.DELIVERED:
            from apps.orders.services.order import OrderService
            OrderService.mark_vendor_order_delivered(shipment.vendor_order.id)
            
        elif new_status == Shipment.ShipmentStatus.RETURNED:
            # Future: Restore inventory, trigger refund
            pass
            
        return shipment

    @staticmethod
    @transaction.atomic
    def assign_courier(shipment_id, courier, tracking_number):
        """
        Assigns courier metadata and generates tracking URL via Strategy Pattern.
        """
        shipment = Shipment.objects.select_for_update().get(id=shipment_id)
        
        shipment.courier = courier
        shipment.tracking_number = tracking_number
        
        # Strategy Pattern resolution
        strategy = ManualCourierStrategy() # Evolve this to dynamic routing later
        shipment.tracking_url = strategy.generate_tracking_url(courier, tracking_number)
        
        shipment.save(update_fields=['courier', 'tracking_number', 'tracking_url'])
        
        return shipment
