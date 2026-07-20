from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from decimal import Decimal
import uuid

@dataclass
class PromotionLineDTO:
    """Represents a single promotion applied to an order."""
    promotion_id: uuid.UUID
    promotion_name: str
    discount_amount: Decimal
    is_free_shipping: bool = False
    
@dataclass
class PromotionEvaluationResult:
    """
    Contract between Promotions domain and Checkout domain.
    Passed back after evaluating Cart DTO against all active promotions and user coupons.
    """
    total_discount: Decimal = Decimal('0.00')
    is_free_shipping: bool = False
    applied_promotions: List[PromotionLineDTO] = field(default_factory=list)
    errors: List[str] = field(default_factory=list) # E.g. "Coupon CODE invalid"

@dataclass
class CheckoutContextDTO:
    """
    Passed from Checkout to Promotions to evaluate eligibility.
    """
    user_id: uuid.UUID
    subtotal: Decimal
    items: List[Dict[str, Any]] # e.g. [{"product_id": uuid, "category_id": uuid, "shop_id": uuid, "price": Decimal, "quantity": int}]
    coupon_codes: List[str] = field(default_factory=list)
