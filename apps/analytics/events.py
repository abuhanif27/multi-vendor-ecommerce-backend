from decimal import Decimal
from django.utils import timezone
from apps.analytics.services.analytics import AnalyticsService

def handle_order_completed_event(event):
    """
    Called when Order is captured.
    Updates shop level and marketplace level metrics by delegating to AnalyticsService.
    """
    date_obj = timezone.now().date()
    
    # Update Vendor metrics
    AnalyticsService.increment_shop_metrics(event.shop_id, date_obj, event.gross_total, event.net_total, event.discount_total, is_new_order=True)
    
    # Update Marketplace metrics
    AnalyticsService.increment_shop_metrics(None, date_obj, event.gross_total, event.net_total, event.discount_total, is_new_order=True)
