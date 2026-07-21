from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal

from apps.common.models import UUIDModel, TimeStampedModel
from apps.shops.models import Shop, ProductVariant

class Order(UUIDModel, TimeStampedModel):
    """
    Parent Order representing the buyer's single checkout transaction.
    """
    class OrderStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PAID = 'PAID', 'Paid'
        FAILED = 'FAILED', 'Failed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        REFUNDED = 'REFUNDED', 'Refunded'
        COMPLETED = 'COMPLETED', 'Completed'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='orders'
    )
    
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
        db_index=True
    )
    
    # Financials (Immutable snapshots for the entire cart)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    shipping_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    tax_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # JSON Snapshots of the addresses so they remain immutable if the user deletes their address later
    shipping_address = models.JSONField()
    billing_address = models.JSONField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.id} - {self.user.email} - {self.status}"


class VendorOrder(UUIDModel, TimeStampedModel):
    """
    Child Order (Sub-Order) representing a single vendor's portion of the parent order.
    """
    class FulfillmentStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending (Awaiting Payment)'
        PROCESSING = 'PROCESSING', 'Processing (Paid)'
        SHIPPED = 'SHIPPED', 'Shipped'
        DELIVERED = 'DELIVERED', 'Delivered'
        CANCELLED = 'CANCELLED', 'Cancelled'
        REFUNDED = 'REFUNDED', 'Refunded'

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='vendor_orders'
    )
    shop = models.ForeignKey(
        Shop,
        on_delete=models.PROTECT,
        related_name='vendor_orders'
    )
    
    status = models.CharField(
        max_length=20,
        choices=FulfillmentStatus.choices,
        default=FulfillmentStatus.PENDING,
        db_index=True
    )
    
    # Financials (The cut/portion belonging to this vendor)
    vendor_subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    vendor_shipping = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    vendor_tax = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    vendor_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['order', 'shop'],
                name='unique_vendor_order_per_shop'
            )
        ]

    def __str__(self):
        return f"SubOrder {self.id} - {self.shop.name} - {self.status}"


class OrderItem(UUIDModel, TimeStampedModel):
    """
    Immutable snapshot of the purchased item.
    """
    vendor_order = models.ForeignKey(
        VendorOrder,
        on_delete=models.CASCADE,
        related_name='items'
    )
    
    # Soft link for analytics. Set to NULL if vendor deletes variant.
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='order_items'
    )
    
    # IMMUTABLE SNAPSHOTS
    product_name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100)
    variant_attributes = models.JSONField(default=dict, blank=True)
    shop_name = models.CharField(max_length=255)
    image_url = models.CharField(max_length=500, blank=True)
    
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    item_total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.quantity}x {self.product_name} ({self.sku})"

class ReturnStatus(models.TextChoices):
    REQUESTED = 'REQUESTED', 'Return Requested'
    APPROVED = 'APPROVED', 'Return Approved'
    SHIPPED = 'SHIPPED', 'Item Shipped Back'
    RECEIVED = 'RECEIVED', 'Item Received by Vendor'
    REJECTED = 'REJECTED', 'Return Rejected'

class Return(UUIDModel, TimeStampedModel):
    vendor_order = models.ForeignKey(VendorOrder, on_delete=models.PROTECT, related_name='returns')
    status = models.CharField(max_length=20, choices=ReturnStatus.choices, default=ReturnStatus.REQUESTED)
    reason = models.TextField()
    tracking_number = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Return {self.id} for VendorOrder {self.vendor_order.id} - {self.status}"

class ReturnItem(UUIDModel, TimeStampedModel):
    return_request = models.ForeignKey(Return, on_delete=models.CASCADE, related_name='items')
    order_item = models.ForeignKey(OrderItem, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    
    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.quantity}x {self.order_item.product_name} (Return {self.return_request.id})"
