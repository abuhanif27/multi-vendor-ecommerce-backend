from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging
from apps.payments.models import Payment

logger = logging.getLogger(__name__)

@shared_task
def expire_pending_payments_task():
    """
    Scans for payments that have been PENDING for more than 30 minutes.
    Marks them as FAILED.
    """
    expiration_threshold = timezone.now() - timedelta(minutes=30)
    
    expired_payments = Payment.objects.filter(
        status=Payment.PaymentStatus.PENDING,
        created_at__lt=expiration_threshold
    )
    
    count = expired_payments.update(
        status=Payment.PaymentStatus.FAILED,
        failure_reason="Payment timed out.",
        updated_at=timezone.now()
    )
    
    if count > 0:
        logger.info(f"expire_pending_payments_task completed. Expired {count} payments.")
