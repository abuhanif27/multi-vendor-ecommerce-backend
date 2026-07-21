from dataclasses import dataclass
from datetime import datetime

@dataclass
class VendorApprovedEvent:
    shop_id: str
    vendor_id: int
    actor_id: int
    occurred_at: datetime

@dataclass
class VendorSuspendedEvent:
    shop_id: str
    vendor_id: int
    actor_id: int
    occurred_at: datetime
    reason: str

@dataclass
class VendorRestoredEvent:
    shop_id: str
    vendor_id: int
    actor_id: int
    occurred_at: datetime

@dataclass
class VendorRejectedEvent:
    shop_id: str
    vendor_id: int
    actor_id: int
    occurred_at: datetime
    reason: str

@dataclass
class ProductApprovedEvent:
    product_id: str
    shop_id: str
    vendor_id: int
    actor_id: int
    occurred_at: datetime

@dataclass
class ProductRejectedEvent:
    product_id: str
    shop_id: str
    vendor_id: int
    actor_id: int
    occurred_at: datetime
    reason: str

@dataclass
class ProductSuspendedEvent:
    product_id: str
    shop_id: str
    vendor_id: int
    actor_id: int
    occurred_at: datetime
    reason: str

@dataclass
class ProductRestoredEvent:
    product_id: str
    shop_id: str
    vendor_id: int
    actor_id: int
    occurred_at: datetime

@dataclass
class ProductReviewModeratedEvent:
    review_id: str
    product_id: str
    new_status: str
    actor_id: int
    occurred_at: datetime
    reason: Optional[str] = None

@dataclass
class ShopReviewModeratedEvent:
    review_id: str
    shop_id: str
    new_status: str
    actor_id: int
    occurred_at: datetime
    reason: Optional[str] = None
