from decimal import Decimal
from django.db.models import F
from django.utils import timezone
from datetime import timedelta
from typing import Optional
from django.db import transaction

from apps.analytics.models import ShopMetricRollup, ProductVelocityRollup, MetricPeriod
# Note: we assume Domain Events like OrderCompletedEvent are defined in the orders/events.py or similar.
# Since we are mock-implementing handlers here for Phase 2:

def get_period_boundaries(date_obj, period: MetricPeriod):
    if period == MetricPeriod.DAILY:
        return date_obj, date_obj
    if period == MetricPeriod.MONTHLY:
        start = date_obj.replace(day=1)
        if start.month == 12:
            end = start.replace(year=start.year+1, month=1, day=1) - timedelta(days=1)
        else:
            end = start.replace(month=start.month+1, day=1) - timedelta(days=1)
        return start, end
    if period == MetricPeriod.ALL_TIME:
        return None, None
    # Weekly/Yearly omitted for brevity but follow similar logic
    return date_obj, date_obj

def update_shop_metric(shop_id: Optional[str], event_date, gross: Decimal, net: Decimal, discount: Decimal, is_new_order: bool = True):
    """
    Increments metrics atomically. Runs synchronously on event emission.
    """
    periods = [MetricPeriod.DAILY, MetricPeriod.MONTHLY, MetricPeriod.ALL_TIME]
    
    for period in periods:
        start, end = get_period_boundaries(event_date, period)
        
        # We use select_for_update or F() expressions. Using get_or_create then F()
        with transaction.atomic():
            rollup, created = ShopMetricRollup.objects.select_for_update().get_or_create(
                shop_id=shop_id,
                period=period,
                period_start=start,
                period_end=end,
                defaults={
                    'gross_revenue': Decimal('0.00'),
                    'net_revenue': Decimal('0.00'),
                    'order_count': 0,
                    'total_discount_amount': Decimal('0.00')
                }
            )
            
            rollup.gross_revenue = F('gross_revenue') + gross
            rollup.net_revenue = F('net_revenue') + net
            rollup.total_discount_amount = F('total_discount_amount') + discount
            if is_new_order:
                rollup.order_count = F('order_count') + 1
                
            rollup.save(update_fields=['gross_revenue', 'net_revenue', 'total_discount_amount', 'order_count'])
            
            # Invalidate Redis cache here
            # cache.delete(f'analytics:{shop_id}:{period}')

def handle_order_completed_event(event):
    """
    Called when Order is captured.
    Updates shop level and marketplace level.
    """
    date_obj = timezone.now().date()
    
    # Update Vendor metrics
    update_shop_metric(event.shop_id, date_obj, event.gross_total, event.net_total, event.discount_total, is_new_order=True)
    
    # Update Marketplace metrics
    update_shop_metric(None, date_obj, event.gross_total, event.net_total, event.discount_total, is_new_order=True)
    
    # Product Velocity could be updated here similarly by iterating over event.items
