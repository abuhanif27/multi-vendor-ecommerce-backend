from django.db import transaction
from django.utils import timezone

from apps.notifications.models import Notification, NotificationDelivery
from apps.notifications.channels.in_app import InAppChannel
from apps.notifications.channels.email import EmailChannel
from apps.notifications.channels.sms import SMSChannel

class NotificationService:
    @staticmethod
    @transaction.atomic
    def dispatch(recipient, title, message, channels, action_url=""):
        """
        Creates the business notification and delivery state records.
        Schedules the async tasks to perform the actual network execution.
        """
        notification = Notification.objects.create(
            recipient=recipient,
            title=title,
            message=message,
            action_url=action_url
        )
        
        from apps.notifications.tasks import send_delivery_task
        
        for channel in channels:
            delivery = NotificationDelivery.objects.create(
                notification=notification,
                channel=channel,
                status=NotificationDelivery.DeliveryStatus.PENDING
            )
            # Dispatch async task. We use transaction.on_commit to ensure
            # the task is only queued if the DB transaction successfully commits.
            transaction.on_commit(lambda d_id=delivery.id: send_delivery_task.delay(d_id))
            
        return notification

    @staticmethod
    def process_delivery(delivery_id):
        """
        Executed by the Celery worker. 
        Routes to the correct strategy and handles idempotency.
        """
        delivery = NotificationDelivery.objects.select_related('notification__recipient').get(id=delivery_id)
        
        # Idempotency lock
        if delivery.status == NotificationDelivery.DeliveryStatus.SENT:
            return delivery
            
        delivery.attempts += 1
        
        strategy_map = {
            NotificationDelivery.DeliveryChannel.IN_APP: InAppChannel(),
            NotificationDelivery.DeliveryChannel.EMAIL: EmailChannel(),
            NotificationDelivery.DeliveryChannel.SMS: SMSChannel(),
        }
        
        strategy = strategy_map.get(delivery.channel)
        if not strategy:
            raise ValueError(f"No strategy found for channel {delivery.channel}")
            
        try:
            strategy.send(delivery)
            delivery.status = NotificationDelivery.DeliveryStatus.SENT
            delivery.sent_at = timezone.now()
        except Exception as e:
            delivery.last_error = str(e)
            # We let the caller (Celery) catch this to trigger a retry
            delivery.save(update_fields=['attempts', 'last_error'])
            raise e
            
        delivery.save(update_fields=['attempts', 'status', 'sent_at'])
        return delivery

    @staticmethod
    @transaction.atomic
    def mark_delivery_failed(delivery_id, error_message):
        """
        Called when Celery exhausts all retry attempts.
        """
        delivery = NotificationDelivery.objects.get(id=delivery_id)
        delivery.status = NotificationDelivery.DeliveryStatus.FAILED
        delivery.last_error = error_message
        delivery.save(update_fields=['status', 'last_error'])
        return delivery
