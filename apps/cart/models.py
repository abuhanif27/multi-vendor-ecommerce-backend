import uuid
from django.db import models
from django.conf import settings
from django.db.models import Q
from apps.common.models import UUIDModel, TimeStampedModel

class Cart(UUIDModel, TimeStampedModel):
    class CartStatus(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        CHECKED_OUT = "CHECKED_OUT", "Checked Out"
        ABANDONED = "ABANDONED", "Abandoned"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="carts"
    )
    status = models.CharField(
        max_length=20,
        choices=CartStatus.choices,
        default=CartStatus.ACTIVE
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(status="ACTIVE"),
                name="unique_active_cart"
            )
        ]

    def __str__(self):
        return f"Cart {self.id} for {self.user.email} ({self.status})"


class CartItem(UUIDModel, TimeStampedModel):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items"
    )
    variant = models.ForeignKey(
        "shops.ProductVariant",
        on_delete=models.CASCADE,
        related_name="cart_items"
    )
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Price snapshot at the time of adding to cart"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "variant"],
                name="unique_cart_variant"
            )
        ]

    def __str__(self):
        return f"{self.quantity} x {self.variant.sku} in Cart {self.cart.id}"
