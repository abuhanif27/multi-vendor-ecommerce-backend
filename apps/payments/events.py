from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class PaymentRefundedEvent:
    refund_id: str
    payment_id: str
    amount: str
    status: str
    occurred_at: datetime
    vendor_order_id: Optional[str] = None
