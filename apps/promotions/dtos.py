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
class CouponRejectionDTO:
    """Structured rejection information for coupons that fail validation."""
    code: str
    reason_code: str
    reason_message: str

@dataclass
class PricingBreakdownDTO:
    """
    Extensible pricing contract. 
    Promotions domain calculates discount_total. 
    Checkout domain can later add shipping_total, tax_total, etc.
    """
    subtotal: Decimal = Decimal('0.00')
    discount_total: Decimal = Decimal('0.00')
    shipping_total: Decimal = Decimal('0.00')
    tax_total: Decimal = Decimal('0.00')
    
    @property
    def grand_total(self) -> Decimal:
        return max(Decimal('0.00'), self.subtotal - self.discount_total + self.shipping_total + self.tax_total)

@dataclass
class PromotionEvaluationResult:
    """
    Contract between Promotions domain and Checkout domain.
    """
    pricing: PricingBreakdownDTO = field(default_factory=PricingBreakdownDTO)
    is_free_shipping: bool = False
    applied_promotions: List[PromotionLineDTO] = field(default_factory=list)
    rejections: List[CouponRejectionDTO] = field(default_factory=list)

@dataclass
class CheckoutContextDTO:
    """
    Passed from Checkout to Promotions to evaluate eligibility.
    """
    user_id: uuid.UUID
    subtotal: Decimal
    items: List[Dict[str, Any]] # e.g. [{"product_id": uuid, "category_id": uuid, "shop_id": uuid, "price": Decimal, "quantity": int}]
    coupon_codes: List[str] = field(default_factory=list)
