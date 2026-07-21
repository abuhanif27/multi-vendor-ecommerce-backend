import logging
from typing import Optional
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework.exceptions import PermissionDenied

from apps.reviews.models import ReviewStatus, ProductReview, ShopReview
from apps.reviews.services.review import ReviewService
from apps.administration.services.audit import AuditService
from apps.notifications.events import EventBus
from apps.administration.events import (
    ProductReviewModeratedEvent,
    ShopReviewModeratedEvent
)

logger = logging.getLogger(__name__)
User = get_user_model()


class ReviewModerationService:
    @staticmethod
    def _enforce_permission(actor: User):
        if not actor.has_perm('administration.can_moderate_reviews'):
            raise PermissionDenied("You do not have permission to moderate reviews.")

    @staticmethod
    def _moderate_review(
        review_id: str, 
        review_type: str, 
        actor: User, 
        new_status: str, 
        reason: Optional[str] = None
    ):
        ReviewModerationService._enforce_permission(actor)
        
        with transaction.atomic():
            if review_type == "product":
                review, state_changed = ReviewService.moderate_product_review(review_id, new_status)
                resource_type = "ProductReview"
                
                event = ProductReviewModeratedEvent(
                    review_id=str(review.id),
                    product_id=str(review.product_id),
                    new_status=new_status,
                    actor_id=actor.id,
                    occurred_at=timezone.now(),
                    reason=reason
                )
            else:
                review, state_changed = ReviewService.moderate_shop_review(review_id, new_status)
                resource_type = "ShopReview"
                
                event = ShopReviewModeratedEvent(
                    review_id=str(review.id),
                    shop_id=str(review.shop_id),
                    new_status=new_status,
                    actor_id=actor.id,
                    occurred_at=timezone.now(),
                    reason=reason
                )

            if not state_changed:
                logger.info(
                    f"{resource_type} moderation skipped (already {new_status})",
                    extra={"review_id": str(review.id), "admin_id": actor.id, "result": "IDEMPOTENT"}
                )
                return review

            AuditService.log_action(
                actor=actor,
                action="UPDATE",
                resource_type=resource_type,
                resource_id=str(review.id),
                result="SUCCESS",
                before_state={"status": review.status},
                after_state={"status": new_status},
                reason=reason
            )

            logger.info(
                f"{resource_type} moderation successful",
                extra={"review_id": str(review.id), "admin_id": actor.id, "new_status": new_status}
            )

            transaction.on_commit(lambda: EventBus.publish(event))

        return review

    @staticmethod
    def hide_product_review(review_id: str, actor: User, reason: str) -> ProductReview:
        return ReviewModerationService._moderate_review(review_id, "product", actor, ReviewStatus.HIDDEN, reason)

    @staticmethod
    def remove_product_review(review_id: str, actor: User, reason: str) -> ProductReview:
        return ReviewModerationService._moderate_review(review_id, "product", actor, ReviewStatus.REMOVED, reason)

    @staticmethod
    def restore_product_review(review_id: str, actor: User, reason: Optional[str] = None) -> ProductReview:
        return ReviewModerationService._moderate_review(review_id, "product", actor, ReviewStatus.PUBLISHED, reason)

    @staticmethod
    def hide_shop_review(review_id: str, actor: User, reason: str) -> ShopReview:
        return ReviewModerationService._moderate_review(review_id, "shop", actor, ReviewStatus.HIDDEN, reason)

    @staticmethod
    def remove_shop_review(review_id: str, actor: User, reason: str) -> ShopReview:
        return ReviewModerationService._moderate_review(review_id, "shop", actor, ReviewStatus.REMOVED, reason)

    @staticmethod
    def restore_shop_review(review_id: str, actor: User, reason: Optional[str] = None) -> ShopReview:
        return ReviewModerationService._moderate_review(review_id, "shop", actor, ReviewStatus.PUBLISHED, reason)
