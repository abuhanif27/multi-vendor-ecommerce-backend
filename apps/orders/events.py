from dataclasses import dataclass
from datetime import datetime

@dataclass
class ReturnRequestedEvent:
    return_id: str
    vendor_order_id: str
    occurred_at: datetime

@dataclass
class ReturnApprovedEvent:
    return_id: str
    vendor_order_id: str
    actor_id: int
    occurred_at: datetime

@dataclass
class ReturnRejectedEvent:
    return_id: str
    vendor_order_id: str
    actor_id: int
    reason: str
    occurred_at: datetime

@dataclass
class ReturnReceivedEvent:
    return_id: str
    vendor_order_id: str
    actor_id: int
    occurred_at: datetime
