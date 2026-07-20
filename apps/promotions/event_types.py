from dataclasses import dataclass
import uuid

@dataclass
class CouponUsageRecordedEvent:
    coupon_code: str
    user_id: uuid.UUID
    order_id: uuid.UUID

@dataclass
class PromotionExhaustedEvent:
    promotion_id: uuid.UUID
    coupon_code: str
