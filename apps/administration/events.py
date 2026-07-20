from dataclasses import dataclass
from datetime import datetime

@dataclass
class VendorApprovedEvent:
    shop_id: str
    vendor_id: int
    approved_by: int
    approved_at: datetime

@dataclass
class VendorSuspendedEvent:
    shop_id: str
    vendor_id: int
    suspended_by: int
    suspended_at: datetime

@dataclass
class VendorRestoredEvent:
    shop_id: str
    vendor_id: int
    restored_by: int
    restored_at: datetime
