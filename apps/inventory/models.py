from django.db import models
from django.conf import settings
from apps.common.models import UUIDModel, TimeStampedModel
from apps.shops.models import ProductVariant


class Inventory(UUIDModel, TimeStampedModel):
    variant = models.OneToOneField(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name="inventory"
    )
    quantity_on_hand = models.PositiveIntegerField(default=0)
    quantity_reserved = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Inventory for {self.variant.sku}"


class InventoryTransaction(UUIDModel, TimeStampedModel):
    class TransactionType(models.TextChoices):
        IN = "IN", "In"
        OUT = "OUT", "Out"
        RESERVE = "RESERVE", "Reserve"
        RELEASE = "RELEASE", "Release"
        ADJUST = "ADJUST", "Adjust"

    inventory = models.ForeignKey(
        Inventory,
        on_delete=models.CASCADE,
        related_name="transactions"
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices
    )
    quantity = models.PositiveIntegerField()
    reference = models.CharField(max_length=255, blank=True)
    note = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inventory_transactions"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.transaction_type} ({self.quantity}) - {self.inventory.variant.sku}"
