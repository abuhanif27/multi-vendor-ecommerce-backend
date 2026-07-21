# Phase 2: Returns Foundation Design

## 1. Objective
Establish a framework to process returns for delivered physical goods. This includes tracking the return lifecycle, orchestrating fulfillment reversal (VendorOrder state), and seamlessly restocking physical inventory.

## 2. Domain Model
Introduce `Return` and `ReturnItem` models within the `orders` domain.

```python
class ReturnStatus(models.TextChoices):
    REQUESTED = 'REQUESTED', 'Return Requested'
    APPROVED = 'APPROVED', 'Return Approved'
    SHIPPED = 'SHIPPED', 'Item Shipped Back'
    RECEIVED = 'RECEIVED', 'Item Received by Vendor'
    REJECTED = 'REJECTED', 'Return Rejected'

class Return(UUIDModel, TimeStampedModel):
    vendor_order = models.ForeignKey(VendorOrder, on_delete=models.PROTECT, related_name='returns')
    status = models.CharField(max_length=20, choices=ReturnStatus.choices, default=ReturnStatus.REQUESTED)
    reason = models.TextField()
    tracking_number = models.CharField(max_length=100, blank=True)

class ReturnItem(UUIDModel, TimeStampedModel):
    return_request = models.ForeignKey(Return, on_delete=models.CASCADE, related_name='items')
    order_item = models.ForeignKey(OrderItem, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    # Ensure quantity <= order_item.quantity
```

## 3. Return Lifecycle (State Machine)
1. **REQUESTED:** A return request is initialized for specific items.
2. **APPROVED/REJECTED:** The vendor reviews the request. (Dispute escalation to Admins is intentionally excluded from this phase and reserved for Phase 3).
3. **SHIPPED:** Buyer provides tracking info and ships it back.
4. **RECEIVED:** Vendor confirms receipt. Inventory is restocked. VendorOrder transitions.

## 4. Service Responsibilities
**`ReturnService` (within Orders domain):**
- `request_return(vendor_order_id, items: list[dict], reason)`: Validates items belong to `vendor_order`, order is `DELIVERED`. Represents normal customer intent.
- `approve_return(return_id, vendor_actor)`: Vendor transitions to `APPROVED`.
- `reject_return(return_id, vendor_actor, reason)`: Vendor transitions to `REJECTED`.
- `mark_return_received(return_id, vendor_actor)`: Vendor confirms receipt. Transitions to `RECEIVED`.
  - Emits a Domain Event which synchronously triggers Inventory Restock and evaluates if `VendorOrder.status` should be updated to `RETURNED`.

**`InventoryService` updates:**
- `restock_inventory(variant_id, quantity)`: Modifies inventory stock physically upon return receipt.

## 5. Event Publication
- **Domain Events (Synchronous within transaction boundary):**
  - `ReturnReceivedEvent`: Coordinates Inventory restocking and Order state updates securely. Failure to execute rolls back the `mark_return_received` transaction.
- **Integration Events (Asynchronous via `on_commit`):**
  - `ReturnRequestedEvent`: Used for sending email/push notifications to the Vendor.
  - `ReturnApprovedEvent`: Used for sending notifications to the Customer.
  - `ReturnRejectedEvent`: Used for sending notifications to the Customer.

## 6. Business Rules & Validations
- Returns can only be initiated on `DELIVERED` VendorOrders.
- Total returned quantity per `OrderItem` across all returns cannot exceed `OrderItem.quantity`.
- Only `RECEIVED` returns restock inventory.

## 7. API Surface (Internal/System)
Internal domain service APIs (e.g., `ReturnService.request_return`) intended for future exposure to Buyer APIs and Admin APIs.
