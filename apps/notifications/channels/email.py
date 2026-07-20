from django.core.mail import send_mail
from django.conf import settings
from apps.notifications.channels.base import BaseChannelStrategy

class EmailChannel(BaseChannelStrategy):
    """
    Sends email using Django's SMTP backend.
    """
    def send(self, delivery):
        notification = delivery.notification
        recipient_email = notification.recipient.email
        
        # Build message
        body = notification.message
        if notification.action_url:
            body += f"\n\nView here: {notification.action_url}"
            
        # This will block and could raise SMTPException if network fails.
        # The Celery task will catch that and trigger a retry.
        send_mail(
            subject=notification.title,
            message=body,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@ecommerce.com'),
            recipient_list=[recipient_email],
            fail_silently=False
        )
