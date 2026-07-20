from celery import shared_task
from apps.notifications.services.notification import NotificationService

@shared_task(bind=True, max_retries=3, default_retry_delay=60) # retries at 1min, 2min, 3min
def send_delivery_task(self, delivery_id):
    """
    Thin Celery task. Routes execution to the NotificationService.
    Handles automatic retries upon network failure.
    """
    try:
        NotificationService.process_delivery(delivery_id)
    except Exception as exc:
        # If we exhausted max retries, mark the delivery as FAILED in the DB.
        if self.request.retries >= self.max_retries:
            NotificationService.mark_delivery_failed(delivery_id, str(exc))
            raise exc
            
        # Otherwise, schedule a retry.
        raise self.retry(exc=exc)
