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
