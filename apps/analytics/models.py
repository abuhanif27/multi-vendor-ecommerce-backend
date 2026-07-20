import uuid
from decimal import Decimal
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.shops.models import Shop, Product

class MetricPeriod(models.TextChoices):
    DAILY = 'DAILY', _('Daily')
    WEEKLY = 'WEEKLY', _('Weekly')
    MONTHLY = 'MONTHLY', _('Monthly')
    YEARLY = 'YEARLY', _('Yearly')
    ALL_TIME = 'ALL_TIME', _('All Time')

class ShopMetricRollup(models.Model):
    """
    Generic rollup table storing aggregated shop metrics.
    Live events increment these numbers atomically.
    Nightly tasks reconcile these numbers against physical orders.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Optional. If null, represents marketplace-wide aggregation.
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, null=True, blank=True, related_name='metric_rollups')
    
    period = models.CharField(max_length=20, choices=MetricPeriod.choices)
    
    # The starting boundary of the period. For ALL_TIME, this can be a fixed epoch or null.
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    
    schema_version = models.PositiveIntegerField(default=1)
    
    # Sales Metrics
    order_count = models.PositiveIntegerField(default=0)
    cancellation_count = models.PositiveIntegerField(default=0)
    return_count = models.PositiveIntegerField(default=0)
    units_sold = models.PositiveIntegerField(default=0)
    
    # Revenue Metrics
    gross_revenue = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    net_revenue = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    total_discount_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    
    # Customer Metrics
    new_customers_count = models.PositiveIntegerField(default=0)
    returning_customers_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['shop', 'period', 'period_start', 'period_end'], 
                name='unique_shop_metric_period_boundaries'
            )
        ]
        indexes = [
            models.Index(fields=['shop', 'period', 'period_start', 'period_end']),
        ]

    def __str__(self):
        shop_name = self.shop.name if self.shop else "Marketplace"
        return f"{shop_name} - {self.period} ({self.period_start} to {self.period_end})"

class ProductVelocityRollup(models.Model):
    """
    Tracks top-selling and lowest-selling products over time.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='product_velocity_rollups')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='velocity_rollups')
    
    period = models.CharField(max_length=20, choices=MetricPeriod.choices)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    
    schema_version = models.PositiveIntegerField(default=1)
    
    units_sold = models.PositiveIntegerField(default=0)
    gross_revenue = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'period', 'period_start', 'period_end'], 
                name='unique_product_velocity_period_boundaries'
            )
        ]
        indexes = [
            models.Index(fields=['shop', 'period', 'period_start', 'period_end']),
            models.Index(fields=['period', 'period_start', 'period_end', 'units_sold']), # Optimize "Top Selling" queries
        ]

    def __str__(self):
        return f"{self.product.name} - {self.period} ({self.period_start} to {self.period_end})"
