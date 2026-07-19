from django.db import models
from apps.common.models import UUIDModel, TimeStampedModel
from apps.orders.models import Order
from decimal import Decimal

class Payment(UUIDModel, TimeStampedModel):
    """
    Represents the financial transaction ledger.
    """
    class Provider(models.TextChoices):
        STRIPE = 'STRIPE', 'Stripe'
        SSLCOMMERZ = 'SSLCOMMERZ', 'SSLCommerz'
        BKASH = 'BKASH', 'bKash'
        NAGAD = 'NAGAD', 'Nagad'
        COD = 'COD', 'Cash on Delivery'

    class PaymentStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        CAPTURED = 'CAPTURED', 'Captured (Paid)'
        FAILED = 'FAILED', 'Failed'
        REFUNDED = 'REFUNDED', 'Refunded'

    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name='payments'
    )
    
    provider = models.CharField(max_length=20, choices=Provider.choices)
    payment_method = models.CharField(max_length=50, blank=True)  # e.g., 'credit_card', 'mobile_money', 'cash'
    
    # External gateway IDs
    provider_reference = models.CharField(max_length=255, blank=True)
    idempotency_key = models.UUIDField(unique=True)
    
    # Financials
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="BDT")
    
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )
    
    # Timestamps & Auditing
    paid_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True)
    raw_metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.id} for Order {self.order.id} - {self.status}"
