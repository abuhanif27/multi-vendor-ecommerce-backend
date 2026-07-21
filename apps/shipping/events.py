from dataclasses import dataclass
from datetime import datetime

@dataclass
class ShipmentDeliveredEvent:
    shipment_id: str
    vendor_order_id: str
    occurred_at: datetime
