from apps.notifications.channels.base import BaseChannelStrategy
import logging

logger = logging.getLogger(__name__)

class SMSChannel(BaseChannelStrategy):
    """
    Placeholder for SMS integration (e.g., Twilio).
    """
    def send(self, delivery):
        # We would use an API client here.
        # client.messages.create(body=delivery.notification.message, to=recipient_phone)
        logger.info(f"Simulating SMS to {delivery.notification.recipient.id}")
