from django.db import models
from apps.common.models import UUIDModel, TimeStampedModel
from apps.orders.models import VendorOrder

class Courier(UUIDModel, TimeStampedModel):
    """
    Represents a shipping carrier.
    """
    name = models.CharField(max_length=100, unique=True)
    tracking_url_template = models.URLField(
        blank=True, 
        help_text="Template for tracking URL, e.g., 'https://courier.com/track?id={tracking_number}'"
    )
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class Shipment(UUIDModel, TimeStampedModel):
    """
    Represents the physical delivery of a package.
    """
    class ShipmentStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        READY_FOR_PICKUP = 'READY_FOR_PICKUP', 'Ready for Pickup'
        SHIPPED = 'SHIPPED', 'Shipped'
        OUT_FOR_DELIVERY = 'OUT_FOR_DELIVERY', 'Out for Delivery'
        DELIVERED = 'DELIVERED', 'Delivered'
        FAILED_DELIVERY = 'FAILED_DELIVERY', 'Failed Delivery'
        RETURNED = 'RETURNED', 'Returned to Sender'

    vendor_order = models.ForeignKey(
        VendorOrder,
        on_delete=models.CASCADE,
        related_name='shipments'
    )
    
    courier = models.ForeignKey(
        Courier,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='shipments'
    )
    
    tracking_number = models.CharField(max_length=100, blank=True)
    tracking_url = models.URLField(blank=True)
    
    # Store the exact address text printed on the label, independent of user profile changes
    shipping_address_snapshot = models.JSONField()
    
    status = models.CharField(
        max_length=20,
        choices=ShipmentStatus.choices,
        default=ShipmentStatus.PENDING
    )
    
    estimated_delivery_date = models.DateField(null=True, blank=True)
    actual_delivery_date = models.DateTimeField(null=True, blank=True)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Shipment {self.id} for VendorOrder {self.vendor_order.id}"

class ShipmentTrackingEvent(UUIDModel, TimeStampedModel):
    """
    Stores the historical timeline of the shipment.
    """
    shipment = models.ForeignKey(
        Shipment,
        on_delete=models.CASCADE,
        related_name='tracking_events'
    )
    status = models.CharField(max_length=20, choices=Shipment.ShipmentStatus.choices)
    location = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.shipment.id} - {self.status} at {self.created_at}"
