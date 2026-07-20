import logging
from typing import Optional
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.shops.models import Shop
from apps.shops.services.shops import ShopService
from apps.administration.services.audit import AuditService
from apps.administration.events import VendorApprovedEvent
from apps.notifications.events import EventBus

User = get_user_model()
logger = logging.getLogger(__name__)

class VendorAdministrationService:
    @staticmethod
    def approve_vendor(shop_id: str, actor: User, reason: Optional[str] = None) -> Shop:
        """
        Orchestrates vendor approval.
        Enforces permissions, idempotency, auditing, and events.
        """
        if not actor.has_perm('administration.can_approve_vendor'):
            raise PermissionDenied("You do not have permission to approve vendors.")

        with transaction.atomic():
            # Domain logic validation and execution
            shop, was_approved_now = ShopService.approve_shop(shop_id)

            if not was_approved_now:
                # Idempotency achieved; nothing actually changed
                logger.info(
                    "Vendor approval skipped (already approved)",
                    extra={"shop_id": str(shop.id), "vendor_id": str(shop.owner_id), "admin_id": actor.id, "result": "IDEMPOTENT"}
                )
                return shop

            # Audit record
            AuditService.log_action(
                actor=actor,
                action="APPROVE",
                resource_type="Shop",
                resource_id=str(shop.id),
                result="SUCCESS",
                before_state={"status": Shop.ShopStatus.PENDING},  # Or SUSPENDED, simplified for now
                after_state={"status": shop.status},
                reason=reason
            )

            logger.info(
                "Vendor approval successful",
                extra={"shop_id": str(shop.id), "vendor_id": str(shop.owner_id), "admin_id": actor.id, "result": "SUCCESS"}
            )

            # Publish event post-commit
            event = VendorApprovedEvent(
                shop_id=str(shop.id),
                vendor_id=shop.owner_id,
                approved_by=actor.id,
                approved_at=timezone.now()
            )
            transaction.on_commit(lambda: EventBus.publish(event))

        return shop
