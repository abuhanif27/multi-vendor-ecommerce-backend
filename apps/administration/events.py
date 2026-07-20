from dataclasses import dataclass
from datetime import datetime

@dataclass
class VendorApprovedEvent:
    shop_id: str
    vendor_id: int
    approved_by: int
    approved_at: datetime
