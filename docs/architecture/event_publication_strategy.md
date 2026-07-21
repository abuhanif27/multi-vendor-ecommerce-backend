# Event Publication Strategy

The system utilizes an EventBus to decouple domains. However, not all events serve the same architectural purpose. Applying a single global publication strategy (e.g., strictly `transaction.on_commit` or strictly synchronous) leads to either data inconsistency or race conditions.

Events in this architecture are strictly classified into a three-tier taxonomy:

## 1. Domain Events
**Purpose:** To coordinate core business state changes across different aggregates. These enforce strong business invariants.

**Behavior:**
- **Execution:** Synchronous. Published directly inside the active transaction block (`EventBus.publish(event)`).
- **Failure Policy:** Failures in downstream subscribers **must** roll back the upstream transaction to guarantee data consistency. If the domain listener crashes, the entire workflow is aborted.

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
- `ShipmentDeliveredEvent`: Consumed by the Orders domain to mark the `VendorOrder` and parent `Order` as complete. A delivered shipment must guarantee a delivered order.

---

## 2. Application Events
**Purpose:** To manage internal infrastructure concerns. These events inform auxiliary subsystems about data mutations.

**Behavior:**
- **Execution:** Asynchronous/Deferred. Published via `transaction.on_commit(lambda: EventBus.publish(event))` or handled out-of-band.
- **Failure Policy:** Failures in downstream subscribers are **logged** but must **never** roll back the completed core business transaction.

**Current Examples:**
- Cache invalidation
- Read model / CQRS projections refresh
- Internal audit projections

---

## 3. Integration Events
**Purpose:** To trigger external side effects, cross-system integrations, or asynchronous job delegation.

**Behavior:**
- **Execution:** Strictly post-commit. Published exclusively using `transaction.on_commit(lambda: EventBus.publish(event))`. This prevents phantom side effects (e.g., dispatching an email for a transaction that ultimately rolled back).
- **Failure Policy:** Failures must not roll back committed data. Subscribers usually delegate to reliable queues (like Celery) which provide their own retry mechanisms.

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
- **Notifications & Webhooks:** `VendorApprovedEvent`, `VendorSuspendedEvent`, `VendorRestoredEvent`, `VendorRejectedEvent`
- **Analytics:** `CouponUsageRecordedEvent`, `PromotionExhaustedEvent`
- **Asynchronous Task Delegation:** `ProductReviewChangedEvent`, `ShopReviewChangedEvent` (These dispatch Celery `.delay()` tasks. The transaction must commit first so the Celery worker can read the new review from the database).
- **Search Indexing**

---

> **Note:** This taxonomy is the platform standard. Future domains must follow this EventBus publication strategy unless there is a demonstrated business reason not to.
