from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging
from apps.orders.models import Order
from apps.orders.services.order import OrderService

logger = logging.getLogger(__name__)

@shared_task
def expire_abandoned_orders_task():
    """
    Scans for orders that have been PENDING for more than 30 minutes.
    Delegates cancellation to OrderService, which naturally cascades to InventoryService.
    """
    expiration_threshold = timezone.now() - timedelta(minutes=30)
    
    abandoned_orders = Order.objects.filter(
        status=Order.OrderStatus.PENDING,
        created_at__lt=expiration_threshold
    )
    
    count = 0
    for order in abandoned_orders:
        try:
            OrderService.cancel_order(order.id)
            count += 1
            logger.info(f"Abandoned order cancelled successfully: {order.id}")
        except Exception as e:
            logger.error(f"Failed to cancel abandoned order {order.id}: {str(e)}")
            
    if count > 0:
        logger.info(f"expire_abandoned_orders_task completed. Cancelled {count} orders.")
