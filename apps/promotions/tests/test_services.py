import uuid
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.promotions.models import (
    Promotion, Coupon, PromotionCondition, ConditionType, 
    PromotionReward, RewardType, PromotionStatus, CouponUsage
)
from apps.promotions.dtos import CheckoutContextDTO
from apps.promotions.services.promotion import PromotionService
from apps.shops.models import Shop, Product, Category
from apps.orders.models import Order

User = get_user_model()

class PromotionServiceTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="test@example.com", password="pwd")
        self.shop = Shop.objects.create(owner=self.user, name="Test Shop")
        self.category = Category.objects.create(name="Electronics")
        self.product = Product.objects.create(shop=self.shop, category=self.category, name="Laptop")
        
        self.order = Order.objects.create(
            user=self.user,
            status=Order.OrderStatus.PENDING,
            shipping_address={},
            subtotal=1000,
            grand_total=1000
        )

        # Basic $10 off promotion
        self.promo = Promotion.objects.create(
            name="Winter Sale",
            status=PromotionStatus.ACTIVE,
            priority=10
        )
        self.coupon = Coupon.objects.create(
            promotion=self.promo,
            code="WINTER10",
            max_uses=10,
            max_uses_per_user=1
        )
        PromotionReward.objects.create(
            promotion=self.promo,
            reward_type=RewardType.FIXED_AMOUNT,
            fixed_amount=Decimal('10.00')
        )
        
        # 15% off Exclusive Automatic Promo
        self.exclusive_promo = Promotion.objects.create(
            name="Exclusive Auto",
            status=PromotionStatus.ACTIVE,
            is_exclusive=True,
            priority=50  # Evaluated first
        )
        PromotionCondition.objects.create(
            promotion=self.exclusive_promo,
            condition_type=ConditionType.MIN_SUBTOTAL,
            min_amount=Decimal('500.00')
        )
        PromotionReward.objects.create(
            promotion=self.exclusive_promo,
            reward_type=RewardType.PERCENTAGE,
            percentage=Decimal('15.00')
        )
        
        self.cart_items = [
            {"product_id": self.product.id, "category_id": self.category.id, "shop_id": self.shop.id, "price": Decimal('1000.00'), "quantity": 1}
        ]

    def test_coupon_validation_success(self):
        context = CheckoutContextDTO(
            user_id=self.user.id,
            subtotal=Decimal('100.00'),
            items=self.cart_items,
            coupon_codes=["WINTER10"]
        )
        # We also have the active automatic promo (min 500 subtotal). Since subtotal is 100, auto promo fails condition.
        result = PromotionService.evaluate_cart(context)
        
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.applied_promotions), 1)
        self.assertEqual(result.total_discount, Decimal('10.00'))

    def test_coupon_validation_invalid_code(self):
        context = CheckoutContextDTO(
            user_id=self.user.id,
            subtotal=Decimal('100.00'),
            items=self.cart_items,
            coupon_codes=["FAKECODE"]
        )
        result = PromotionService.evaluate_cart(context)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("invalid", result.errors[0])
        self.assertEqual(result.total_discount, Decimal('0.00'))

    def test_automatic_promotion_applies(self):
        context = CheckoutContextDTO(
            user_id=self.user.id,
            subtotal=Decimal('1000.00'),
            items=self.cart_items,
            coupon_codes=[]
        )
        # Subtotal > 500, so exclusive auto promo applies. (15% of 1000 = 150)
        result = PromotionService.evaluate_cart(context)
        
        self.assertEqual(len(result.applied_promotions), 1)
        self.assertEqual(result.applied_promotions[0].promotion_id, self.exclusive_promo.id)
        self.assertEqual(result.total_discount, Decimal('150.00'))

    def test_exclusive_stacking_resolution(self):
        context = CheckoutContextDTO(
            user_id=self.user.id,
            subtotal=Decimal('1000.00'),
            items=self.cart_items,
            coupon_codes=["WINTER10"]
        )
        # Both apply, but exclusive auto promo has priority 50 vs priority 10 for WINTER10.
        # Since priority 50 is exclusive, WINTER10 should be discarded.
        result = PromotionService.evaluate_cart(context)
        
        self.assertEqual(len(result.applied_promotions), 1)
        self.assertEqual(result.applied_promotions[0].promotion_id, self.exclusive_promo.id)
        self.assertEqual(result.total_discount, Decimal('150.00'))
        
    def test_consume_coupon_success(self):
        PromotionService.consume_coupon("WINTER10", self.user.id, self.order.id)
        
        self.coupon.refresh_from_db()
        self.assertEqual(self.coupon.current_uses, 1)
        self.assertEqual(CouponUsage.objects.count(), 1)
        
    def test_consume_coupon_max_uses_per_user(self):
        PromotionService.consume_coupon("WINTER10", self.user.id, self.order.id)
        
        order2 = Order.objects.create(user=self.user, status=Order.OrderStatus.PENDING, shipping_address={}, subtotal=1, grand_total=1)
        
        with self.assertRaises(ValidationError) as context:
            PromotionService.consume_coupon("WINTER10", self.user.id, order2.id)
            
        self.assertIn("maximum allowed times", str(context.exception))
