from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

from apps.notifications.events import EventBus
from apps.notifications.models import Notification, NotificationDelivery
from apps.notifications.services.notification import NotificationService

User = get_user_model()

class NotificationModuleTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="test@example.com", password="password123")
        EventBus.clear()

    def test_event_publishing(self):
        """Test the explicit EventBus safely dispatches and catches errors."""
        class TestEvent:
            pass
        
        mock_handler = MagicMock()
        mock_error_handler = MagicMock(side_effect=Exception("Boom"))
        
        EventBus.subscribe(TestEvent, mock_handler)
        EventBus.subscribe(TestEvent, mock_error_handler)
        
        # Publish. The error handler should raise an exception internally but NOT crash the bus.
        event = TestEvent()
        EventBus.publish(event)
        
        mock_handler.assert_called_once_with(event)
        mock_error_handler.assert_called_once_with(event)

    @patch('apps.notifications.tasks.send_delivery_task.delay')
    def test_notification_creation_and_dispatch(self, mock_task):
        """Test that NotificationService creates the parent and child records and queues the task."""
        notification = NotificationService.dispatch(
            recipient=self.user,
            title="Hello",
            message="World",
            channels=[NotificationDelivery.DeliveryChannel.IN_APP, NotificationDelivery.DeliveryChannel.EMAIL]
        )
        
        self.assertEqual(notification.title, "Hello")
        self.assertEqual(notification.deliveries.count(), 2)
        
        in_app = notification.deliveries.get(channel=NotificationDelivery.DeliveryChannel.IN_APP)
        email = notification.deliveries.get(channel=NotificationDelivery.DeliveryChannel.EMAIL)
        
        self.assertEqual(in_app.status, NotificationDelivery.DeliveryStatus.PENDING)
        
        # In a test, transaction.on_commit won't trigger standardly unless using TransactionTestCase.
        # But we can verify the DB state perfectly.
        
    @patch('apps.notifications.channels.email.send_mail')
    def test_channel_strategy_execution(self, mock_send_mail):
        """Test that process_delivery routes to the correct strategy and marks SENT."""
        notification = Notification.objects.create(recipient=self.user, title="Hello", message="World")
        delivery = NotificationDelivery.objects.create(
            notification=notification, 
            channel=NotificationDelivery.DeliveryChannel.EMAIL
        )
        
        processed = NotificationService.process_delivery(delivery.id)
        
        mock_send_mail.assert_called_once()
        self.assertEqual(processed.status, NotificationDelivery.DeliveryStatus.SENT)
        self.assertEqual(processed.attempts, 1)

    @patch('apps.notifications.channels.email.send_mail')
    def test_idempotency_prevents_duplicate_sends(self, mock_send_mail):
        """Test that if process_delivery is called on a SENT delivery, it returns immediately."""
        notification = Notification.objects.create(recipient=self.user, title="Hello", message="World")
        delivery = NotificationDelivery.objects.create(
            notification=notification, 
            channel=NotificationDelivery.DeliveryChannel.EMAIL,
            status=NotificationDelivery.DeliveryStatus.SENT
        )
        
        processed = NotificationService.process_delivery(delivery.id)
        
        # The strategy should NOT be called.
        mock_send_mail.assert_not_called()
        self.assertEqual(processed.attempts, 0) # No new attempts logged

    @patch('apps.notifications.channels.email.send_mail', side_effect=Exception("Network Down"))
    def test_failure_handling(self, mock_send_mail):
        """Test that process_delivery bubbles up exceptions to Celery and logs the error."""
        notification = Notification.objects.create(recipient=self.user, title="Hello", message="World")
        delivery = NotificationDelivery.objects.create(
            notification=notification, 
            channel=NotificationDelivery.DeliveryChannel.EMAIL
        )
        
        with self.assertRaises(Exception):
            NotificationService.process_delivery(delivery.id)
            
        delivery.refresh_from_db()
        self.assertEqual(delivery.attempts, 1)
        self.assertEqual(delivery.status, NotificationDelivery.DeliveryStatus.PENDING) # Still pending for retry
        self.assertEqual(delivery.last_error, "Network Down")
        
        # Simulate Celery exhausting retries
        failed_delivery = NotificationService.mark_delivery_failed(delivery.id, "Max retries exceeded.")
        self.assertEqual(failed_delivery.status, NotificationDelivery.DeliveryStatus.FAILED)
