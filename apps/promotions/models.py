import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from apps.shops.models import Shop, Product
from apps.catalog.models import Category
from apps.orders.models import Order

User = get_user_model()

class PromotionStatus(models.TextChoices):
    DRAFT = 'DRAFT', _('Draft')
    ACTIVE = 'ACTIVE', _('Active')
    PAUSED = 'PAUSED', _('Paused')
    EXPIRED = 'EXPIRED', _('Expired')
    ARCHIVED = 'ARCHIVED', _('Archived')

class Promotion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=PromotionStatus.choices, default=PromotionStatus.DRAFT)
    
    # If null, it's a marketplace-wide promotion. If set, restricts to specific shop
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, null=True, blank=True, related_name='promotions')
    
    # Stackability
    priority = models.IntegerField(default=0, help_text="Higher numbers are evaluated first.")
    is_exclusive = models.BooleanField(default=False, help_text="If true, no other promotions can stack with this.")
    
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['status', 'start_date', 'end_date']),
            models.Index(fields=['priority']),
        ]

    def __str__(self):
        return f"{self.name} ({self.status})"

class Coupon(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name='coupons')
    code = models.CharField(max_length=50, unique=True, db_index=True)
    
    max_uses = models.PositiveIntegerField(null=True, blank=True, help_text="Null for unlimited uses.")
    
    # Denormalized optimization. True source of truth is CouponUsage count.
    current_uses = models.PositiveIntegerField(default=0)
    
    max_uses_per_user = models.PositiveIntegerField(default=1, help_text="Max times a single user can use this coupon.")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.code

class ConditionType(models.TextChoices):
    MIN_SUBTOTAL = 'MIN_SUBTOTAL', _('Minimum Subtotal')
    NEW_CUSTOMER = 'NEW_CUSTOMER', _('New Customer Only')
    SPECIFIC_CATEGORY = 'SPECIFIC_CATEGORY', _('Specific Category')
    SPECIFIC_PRODUCT = 'SPECIFIC_PRODUCT', _('Specific Product')
    GENERIC_CONFIG = 'GENERIC_CONFIG', _('Generic JSON Config')

class PromotionCondition(models.Model):
    """
    Explicit fields for common conditions, with fallback to JSON for complex logic.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name='conditions')
    
    condition_type = models.CharField(max_length=50, choices=ConditionType.choices)
    
    # Explicit fields
    min_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    
    # Complex configurations
    config = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.promotion.name} - {self.condition_type}"

class RewardType(models.TextChoices):
    FIXED_AMOUNT = 'FIXED_AMOUNT', _('Fixed Amount Discount')
    PERCENTAGE = 'PERCENTAGE', _('Percentage Discount')
    FREE_SHIPPING = 'FREE_SHIPPING', _('Free Shipping')

class PromotionReward(models.Model):
    """
    Explicit fields for rewards.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    promotion = models.OneToOneField(Promotion, on_delete=models.CASCADE, related_name='reward')
    
    reward_type = models.CharField(max_length=50, choices=RewardType.choices)
    
    # Explicit fields
    fixed_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    max_discount_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    config = models.JSONField(default=dict, blank=True)
    
    def __str__(self):
        return f"{self.promotion.name} - {self.reward_type}"

class CouponUsage(models.Model):
    """
    The absolute source of truth for coupon redemptions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    coupon = models.ForeignKey(Coupon, on_delete=models.PROTECT, related_name='usages')
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='coupon_usages')
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name='coupon_usages')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['coupon', 'user', 'order'], name='unique_coupon_usage_per_order')
        ]
        indexes = [
            models.Index(fields=['coupon', 'user']),
        ]

    def __str__(self):
        return f"{self.coupon.code} used by {self.user.email}"
