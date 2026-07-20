from dataclasses import dataclass
import uuid

@dataclass
class OrderPaidEvent:
    order_id: uuid.UUID

@dataclass
class ShipmentDeliveredEvent:
    shipment_id: uuid.UUID
    
@dataclass
class PaymentCapturedEvent:
    payment_id: uuid.UUID
    
@dataclass
class AbandonedOrderCancelledEvent:
    order_id: uuid.UUID
