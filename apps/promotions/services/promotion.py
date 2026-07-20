from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError

from apps.promotions.dtos import (
    CheckoutContextDTO, PromotionEvaluationResult, PromotionLineDTO, 
    CouponRejectionDTO, PricingBreakdownDTO
)
from apps.promotions.models import Promotion, Coupon, PromotionStatus, CouponUsage
from apps.promotions.services.engine import PromotionEngine
from apps.notifications.events import EventBus
from apps.promotions.event_types import CouponUsageRecordedEvent, PromotionExhaustedEvent
from apps.orders.models import Order
from django.contrib.auth import get_user_model

User = get_user_model()

class PromotionService:
    @staticmethod
    def _is_promotion_active(promotion: Promotion) -> bool:
        if promotion.status != PromotionStatus.ACTIVE:
            return False
        now = timezone.now()
        if promotion.start_date and promotion.start_date > now:
            return False
        if promotion.end_date and promotion.end_date < now:
            return False
        return True

    @classmethod
    def evaluate_cart(cls, context: CheckoutContextDTO) -> PromotionEvaluationResult:
        """
        Read-only evaluation pipeline.
        Fetches relevant promotions, verifies conditions, resolves conflicts, and calculates discount.
        """
        result = PromotionEvaluationResult()
        result.pricing.subtotal = context.subtotal
        
        # 1. Fetch relevant user-supplied coupons
        valid_coupons = []
        for code in context.coupon_codes:
            try:
                coupon = Coupon.objects.select_related('promotion', 'promotion__reward').prefetch_related('promotion__conditions').get(code=code)
                # Max uses check
                if coupon.max_uses and coupon.current_uses >= coupon.max_uses:
                    result.rejections.append(CouponRejectionDTO(code, "MAX_USES_REACHED", "Coupon has reached its usage limit."))
                    continue
                # Per user limit check
                user_uses = CouponUsage.objects.filter(coupon=coupon, user_id=context.user_id).count()
                if coupon.max_uses_per_user and user_uses >= coupon.max_uses_per_user:
                    result.rejections.append(CouponRejectionDTO(code, "USER_LIMIT_REACHED", "You have already used this coupon the maximum allowed times."))
                    continue
                    
                if not cls._is_promotion_active(coupon.promotion):
                    result.rejections.append(CouponRejectionDTO(code, "INACTIVE", "Coupon is not currently active."))
                    continue
                    
                valid_coupons.append(coupon)
            except Coupon.DoesNotExist:
                result.rejections.append(CouponRejectionDTO(code, "INVALID_CODE", "Coupon is invalid."))

        # Extract promotions from valid coupons
        promotions = [c.promotion for c in valid_coupons]
        
        # 2. Add automatic marketplace promotions
        # Normally we'd cache this query in Redis.
        automatic_promos = Promotion.objects.filter(
            status=PromotionStatus.ACTIVE,
            coupons__isnull=True # Automatic promos don't have coupons
        ).select_related('reward').prefetch_related('conditions')
        
        for promo in automatic_promos:
            if cls._is_promotion_active(promo):
                promotions.append(promo)
                
        # 3. Filter by Conditions
        eligible_promotions = []
        for promo in promotions:
            conditions_met = True
            for condition in promo.conditions.all():
                if not PromotionEngine.evaluate_condition(condition, context):
                    conditions_met = False
                    break
            
            # Check vendor restriction if shop is set
            if promo.shop_id:
                # Promotion only applies if the cart contains items from this shop
                if not any(str(item.get('shop_id')) == str(promo.shop_id) for item in context.items):
                    conditions_met = False

            if conditions_met:
                eligible_promotions.append(promo)

        # 4. Conflict Resolution (Stacking Rules) & Deterministic Sorting
        # Sort priority descending, then UUID ascending to break ties
        eligible_promotions.sort(key=lambda p: (-p.priority, str(p.id)))
        
        current_subtotal = context.subtotal
        
        for promo in eligible_promotions:
            if not hasattr(promo, 'reward'):
                continue
                
            reward_res = PromotionEngine.calculate_reward(promo.reward, context, current_subtotal)
            discount = reward_res['discount']
            is_free_shipping = reward_res['is_free_shipping']
            
            if discount > 0 or is_free_shipping:
                result.applied_promotions.append(PromotionLineDTO(
                    promotion_id=promo.id,
                    promotion_name=promo.name,
                    discount_amount=discount,
                    is_free_shipping=is_free_shipping
                ))
                result.pricing.discount_total += discount
                if is_free_shipping:
                    result.is_free_shipping = True
                    
                current_subtotal -= discount
                if current_subtotal < 0:
                    current_subtotal = Decimal('0.00')
                    
                if promo.is_exclusive:
                    # Halt stacking
                    break

        return result

    @classmethod
    @transaction.atomic
    def consume_coupon(cls, code: str, user_id: uuid.UUID, order_id: uuid.UUID):
        """
        Mutation pipeline. Called synchronously during checkout's transaction.atomic().
        Acquires row locks to absolutely prevent double redemption.
        """
        try:
            # Row-level lock prevents race conditions
            coupon = Coupon.objects.select_for_update().get(code=code)
        except Coupon.DoesNotExist:
            raise ValidationError(f"Coupon {code} does not exist.")
            
        if coupon.max_uses and coupon.current_uses >= coupon.max_uses:
            raise ValidationError(f"Coupon {code} has reached its usage limit.")
            
        user_uses = CouponUsage.objects.filter(coupon=coupon, user_id=user_id).count()
        if coupon.max_uses_per_user and user_uses >= coupon.max_uses_per_user:
            raise ValidationError(f"You have already used coupon {code} the maximum allowed times.")

        user = User.objects.get(id=user_id)
        order = Order.objects.get(id=order_id)
        
        # Create usage (protected by DB unique constraints as well)
        CouponUsage.objects.create(
            coupon=coupon,
            user=user,
            order=order
        )
        
        # Update denormalized count safely inside lock
        coupon.current_uses += 1
        coupon.save(update_fields=['current_uses'])
        
        # Publish events
        transaction.on_commit(lambda: EventBus.publish(CouponUsageRecordedEvent(
            coupon_code=code,
            user_id=user_id,
            order_id=order_id
        )))
        
        if coupon.max_uses and coupon.current_uses >= coupon.max_uses:
            transaction.on_commit(lambda: EventBus.publish(PromotionExhaustedEvent(
                promotion_id=coupon.promotion_id,
                coupon_code=code
            )))
