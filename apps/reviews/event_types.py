from dataclasses import dataclass
import uuid

@dataclass
class ProductReviewChangedEvent:
    product_id: uuid.UUID

@dataclass
class ShopReviewChangedEvent:
    shop_id: uuid.UUID
