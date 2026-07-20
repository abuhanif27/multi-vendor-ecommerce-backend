from typing import Optional
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from apps.shops.models import Shop
from apps.shops.services.shops import ShopService
from apps.administration.services.audit import AuditService
from apps.administration.events import VendorApprovedEvent
from apps.notifications.events import EventBus

User = get_user_model()

class VendorAdministrationService:
    @staticmethod
    def approve_vendor(shop_id: str, actor: User, reason: Optional[str] = None) -> Shop:
        """
        Orchestrates vendor approval.
        Enforces permissions, idempotency, auditing, and events.
        """
        if not actor.has_perm('administration.can_approve_vendor'):
            raise PermissionDenied("You do not have permission to approve vendors.")

        # Check idempotency prior to transaction to avoid empty audit records
        shop = Shop.objects.get(id=shop_id)
        if shop.status == Shop.ShopStatus.APPROVED:
            return shop

        before_state = {"status": shop.status}

        with transaction.atomic():
            # Domain logic validation and execution
            shop = ShopService.approve_shop(shop_id)

            # Audit record
            AuditService.log_action(
                actor=actor,
                action="APPROVE",
                resource_type="Shop",
                resource_id=str(shop.id),
                result="SUCCESS",
                before_state=before_state,
                after_state={"status": shop.status},
                reason=reason
            )

            # Publish event post-commit
            transaction.on_commit(
                lambda: EventBus.publish(VendorApprovedEvent(shop_id=str(shop.id), admin_id=actor.id))
            )

        return shop
