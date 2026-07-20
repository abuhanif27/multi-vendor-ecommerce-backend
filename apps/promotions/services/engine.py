from decimal import Decimal
from apps.promotions.models import ConditionType, RewardType
from apps.promotions.dtos import CheckoutContextDTO

class ConditionEvaluator:
    def is_satisfied(self, condition, context: CheckoutContextDTO) -> bool:
        raise NotImplementedError

class MinSubtotalEvaluator(ConditionEvaluator):
    def is_satisfied(self, condition, context: CheckoutContextDTO) -> bool:
        if not condition.min_amount:
            return True
        return context.subtotal >= condition.min_amount

class SpecificCategoryEvaluator(ConditionEvaluator):
    def is_satisfied(self, condition, context: CheckoutContextDTO) -> bool:
        if not condition.category_id:
            return True
        # Check if ANY item in cart matches this category
        return any(str(item.get('category_id')) == str(condition.category_id) for item in context.items)

class SpecificProductEvaluator(ConditionEvaluator):
    def is_satisfied(self, condition, context: CheckoutContextDTO) -> bool:
        if not condition.product_id:
            return True
        return any(str(item.get('product_id')) == str(condition.product_id) for item in context.items)

class RewardCalculator:
    def calculate(self, reward, context: CheckoutContextDTO, current_subtotal: Decimal) -> Decimal:
        raise NotImplementedError

class FixedAmountCalculator(RewardCalculator):
    def calculate(self, reward, context: CheckoutContextDTO, current_subtotal: Decimal) -> Decimal:
        if not reward.fixed_amount:
            return Decimal('0.00')
        return min(reward.fixed_amount, current_subtotal)

class PercentageCalculator(RewardCalculator):
    def calculate(self, reward, context: CheckoutContextDTO, current_subtotal: Decimal) -> Decimal:
        if not reward.percentage:
            return Decimal('0.00')
        discount = (reward.percentage / Decimal('100.0')) * current_subtotal
        if reward.max_discount_amount and discount > reward.max_discount_amount:
            return reward.max_discount_amount
        return discount

class FreeShippingCalculator(RewardCalculator):
    def calculate(self, reward, context: CheckoutContextDTO, current_subtotal: Decimal) -> Decimal:
        # Free shipping sets a flag, the explicit "discount" on items is 0
        return Decimal('0.00')

class PromotionEngine:
    _evaluators = {
        ConditionType.MIN_SUBTOTAL: MinSubtotalEvaluator(),
        ConditionType.SPECIFIC_CATEGORY: SpecificCategoryEvaluator(),
        ConditionType.SPECIFIC_PRODUCT: SpecificProductEvaluator(),
    }
    
    _calculators = {
        RewardType.FIXED_AMOUNT: FixedAmountCalculator(),
        RewardType.PERCENTAGE: PercentageCalculator(),
        RewardType.FREE_SHIPPING: FreeShippingCalculator(),
    }

    @classmethod
    def evaluate_condition(cls, condition, context: CheckoutContextDTO) -> bool:
        evaluator = cls._evaluators.get(condition.condition_type)
        if not evaluator:
            # Fallback or generic rule not implemented
            return True
        return evaluator.is_satisfied(condition, context)
        
    @classmethod
    def calculate_reward(cls, reward, context: CheckoutContextDTO, current_subtotal: Decimal) -> dict:
        calculator = cls._calculators.get(reward.reward_type)
        if not calculator:
            return {"discount": Decimal('0.00'), "is_free_shipping": False}
            
        discount = calculator.calculate(reward, context, current_subtotal)
        is_free_shipping = (reward.reward_type == RewardType.FREE_SHIPPING)
        return {"discount": discount, "is_free_shipping": is_free_shipping}
