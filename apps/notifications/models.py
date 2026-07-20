from django.db import models
from django.conf import settings
from apps.common.models import UUIDModel, TimeStampedModel

class Notification(UUIDModel, TimeStampedModel):
    """
    Represents the business notification intended for a user.
    """
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    action_url = models.URLField(blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification to {self.recipient.email}: {self.title}"

class NotificationDelivery(UUIDModel, TimeStampedModel):
    """
    Represents the physical delivery state of a notification over a specific channel.
    """
    class DeliveryChannel(models.TextChoices):
        IN_APP = 'IN_APP', 'In-App'
        EMAIL = 'EMAIL', 'Email'
        SMS = 'SMS', 'SMS'

    class DeliveryStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SENT = 'SENT', 'Sent'
        FAILED = 'FAILED', 'Failed'

    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name='deliveries'
    )
    channel = models.CharField(max_length=20, choices=DeliveryChannel.choices)
    status = models.CharField(max_length=20, choices=DeliveryStatus.choices, default=DeliveryStatus.PENDING)
    provider = models.CharField(max_length=100, blank=True, help_text="e.g. SendGrid, Twilio, Local")
    attempts = models.PositiveIntegerField(default=0)
    sent_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('notification', 'channel') # A notification is sent via a channel exactly once

    def __str__(self):
        return f"{self.channel} delivery for {self.notification.id} - {self.status}"
