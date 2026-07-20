from celery import shared_task
import logging
from django.utils import timezone
from django.db import connection

logger = logging.getLogger(__name__)

@shared_task
def cleanup_expired_tokens_task():
    """
    Cleans up expired blacklisted JWT tokens.
    Uses simplejwt's built in flushexpiredtokens management command logic.
    """
    try:
        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
        
        # Flush expired outstanding tokens
        expired_tokens = OutstandingToken.objects.filter(expires_at__lte=timezone.now())
        count = expired_tokens.count()
        expired_tokens.delete()
        
        if count > 0:
            logger.info(f"cleanup_expired_tokens_task completed. Deleted {count} expired tokens.")
    except ImportError:
        pass # Blacklist app not installed
