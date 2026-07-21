# Event Publication Strategy

The system utilizes an EventBus to decouple domains. However, not all events serve the same architectural purpose. Applying a single global publication strategy (e.g., strictly `transaction.on_commit` or strictly synchronous) leads to either data inconsistency or race conditions.

Events in this architecture are strictly classified into two categories:

## 1. Internal Domain Events (Synchronous Choreography)
**Purpose:** To coordinate state changes across different aggregates within the same database transaction. These enforce strong business invariants where failure in the downstream domain must roll back the upstream domain.

**Strategy:** Publish **synchronously** inside the active transaction block. Do NOT use `transaction.on_commit`.

**Implementation Pattern:**
```python
@transaction.atomic
def complete_shipment():
    shipment.status = DELIVERED
    shipment.save()
    
    # Emitted synchronously. Handlers execute in the same transaction.
    EventBus.publish(ShipmentDeliveredEvent(shipment_id=shipment.id))
```

**Current Examples:**
- `ShipmentDeliveredEvent`: Consumed by the Orders domain to mark the `VendorOrder` and parent `Order` as complete. Must be synchronous to ensure database consistency (a delivered shipment must guarantee a delivered order).

---

## 2. Integration Events (Asynchronous / Side-Effects)
**Purpose:** To trigger external side effects, cross-system integrations, or asynchronous eventual consistency. These must only fire if the database transaction successfully commits to prevent "phantom" side effects (e.g., sending an email for an order that rolled back).

**Strategy:** Publish strictly using **`transaction.on_commit`**. 

**Implementation Pattern:**
```python
@transaction.atomic
def approve_vendor():
    shop.status = APPROVED
    shop.save()
    
    # Emitted post-commit. Handlers trigger side effects safely.
    transaction.on_commit(
        lambda: EventBus.publish(VendorApprovedEvent(shop_id=shop.id))
    )
```

**Current Examples:**
- `VendorApprovedEvent`, `VendorSuspendedEvent`, `VendorRestoredEvent`, `VendorRejectedEvent`: Trigger external notifications (e.g., emails) and webhooks.
- `CouponUsageRecordedEvent`, `PromotionExhaustedEvent`: Typically consumed by Analytics pipelines or marketing integrations.
- `ProductReviewChangedEvent`, `ShopReviewChangedEvent`: These dispatch asynchronous Celery tasks (`.delay()`). The transaction must commit first so the Celery worker can read the new review from the database.
