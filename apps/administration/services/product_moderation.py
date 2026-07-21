import logging
from typing import Optional
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework.exceptions import PermissionDenied

from apps.shops.models import Product
from apps.shops.services import ProductService
from apps.administration.services.audit import AuditService
from apps.notifications.events import EventBus
from apps.administration.events import (
    ProductApprovedEvent,
    ProductRejectedEvent,
    ProductSuspendedEvent,
    ProductRestoredEvent,
)

logger = logging.getLogger(__name__)
User = get_user_model()


class ProductModerationService:
    @staticmethod
    def approve_product(product_id: str, actor: User, reason: Optional[str] = None) -> Product:
        if not actor.has_perm('administration.can_moderate_products'):
            raise PermissionDenied("You do not have permission to approve products.")
            
        with transaction.atomic():
            product, was_approved_now = ProductService.approve_product(product_id)

            if not was_approved_now:
                logger.info(
                    "Product approval skipped (already approved)",
                    extra={"product_id": str(product.id), "admin_id": actor.id, "result": "IDEMPOTENT"}
                )
                return product

            AuditService.log_action(
                actor=actor,
                action="APPROVE",
                resource_type="Product",
                resource_id=str(product.id),
                result="SUCCESS",
                before_state={"status": Product.ProductStatus.PENDING},
                after_state={"status": product.status},
                reason=reason
            )

            logger.info(
                "Product approval successful",
                extra={"product_id": str(product.id), "admin_id": actor.id, "result": "SUCCESS"}
            )

            event = ProductApprovedEvent(
                product_id=str(product.id),
                shop_id=str(product.shop_id),
                vendor_id=product.shop.owner_id,
                actor_id=actor.id,
                occurred_at=timezone.now()
            )
            transaction.on_commit(lambda: EventBus.publish(event))

        return product

    @staticmethod
    def reject_product(product_id: str, actor: User, reason: str) -> Product:
        if not actor.has_perm('administration.can_moderate_products'):
            raise PermissionDenied("You do not have permission to reject products.")
            
        with transaction.atomic():
            product, was_rejected_now = ProductService.reject_product(product_id)

            if not was_rejected_now:
                logger.info("Product rejection skipped", extra={"product_id": str(product.id), "result": "IDEMPOTENT"})
                return product

            AuditService.log_action(
                actor=actor,
                action="REJECT",
                resource_type="Product",
                resource_id=str(product.id),
                result="SUCCESS",
                before_state={"status": Product.ProductStatus.PENDING},
                after_state={"status": product.status},
                reason=reason
            )

            logger.info("Product rejection successful", extra={"product_id": str(product.id), "admin_id": actor.id})

            event = ProductRejectedEvent(
                product_id=str(product.id),
                shop_id=str(product.shop_id),
                vendor_id=product.shop.owner_id,
                actor_id=actor.id,
                occurred_at=timezone.now(),
                reason=reason
            )
            transaction.on_commit(lambda: EventBus.publish(event))

        return product

    @staticmethod
    def suspend_product(product_id: str, actor: User, reason: str) -> Product:
        if not actor.has_perm('administration.can_moderate_products'):
            raise PermissionDenied("You do not have permission to suspend products.")
            
        with transaction.atomic():
            product, was_suspended_now = ProductService.suspend_product(product_id)

            if not was_suspended_now:
                logger.info("Product suspension skipped", extra={"product_id": str(product.id), "result": "IDEMPOTENT"})
                return product

            AuditService.log_action(
                actor=actor,
                action="SUSPEND",
                resource_type="Product",
                resource_id=str(product.id),
                result="SUCCESS",
                before_state={"status": Product.ProductStatus.ACTIVE},
                after_state={"status": product.status},
                reason=reason
            )

            logger.info("Product suspension successful", extra={"product_id": str(product.id), "admin_id": actor.id})

            event = ProductSuspendedEvent(
                product_id=str(product.id),
                shop_id=str(product.shop_id),
                vendor_id=product.shop.owner_id,
                actor_id=actor.id,
                occurred_at=timezone.now(),
                reason=reason
            )
            transaction.on_commit(lambda: EventBus.publish(event))

        return product

    @staticmethod
    def restore_product(product_id: str, actor: User, reason: Optional[str] = None) -> Product:
        if not actor.has_perm('administration.can_moderate_products'):
            raise PermissionDenied("You do not have permission to restore products.")
            
        with transaction.atomic():
            product, was_restored_now = ProductService.restore_product(product_id)

            if not was_restored_now:
                logger.info("Product restoration skipped", extra={"product_id": str(product.id), "result": "IDEMPOTENT"})
                return product

            AuditService.log_action(
                actor=actor,
                action="OTHER", # Note: 'RESTORE' is not in ACTION_CHOICES, 'OTHER' is safer
                resource_type="Product",
                resource_id=str(product.id),
                result="SUCCESS",
                before_state={"status": Product.ProductStatus.SUSPENDED},
                after_state={"status": product.status},
                reason=reason
            )

            logger.info("Product restoration successful", extra={"product_id": str(product.id), "admin_id": actor.id})

            event = ProductRestoredEvent(
                product_id=str(product.id),
                shop_id=str(product.shop_id),
                vendor_id=product.shop.owner_id,
                actor_id=actor.id,
                occurred_at=timezone.now()
            )
            transaction.on_commit(lambda: EventBus.publish(event))

        return product
