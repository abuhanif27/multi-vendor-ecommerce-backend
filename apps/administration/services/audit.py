from typing import Optional, Dict, Any
from django.contrib.auth import get_user_model
from apps.administration.models import AdminAuditLog

User = get_user_model()

class AuditService:
    @staticmethod
    def log_action(
        actor: User,
        action: str,
        resource_type: str,
        resource_id: str,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AdminAuditLog:
        """
        Creates an immutable audit log entry for a privileged staff action.
        """
        log = AdminAuditLog.objects.create(
            actor=actor,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            before_state=before_state,
            after_state=after_state,
            reason=reason,
            ip_address=ip_address,
            user_agent=user_agent
        )
        return log
