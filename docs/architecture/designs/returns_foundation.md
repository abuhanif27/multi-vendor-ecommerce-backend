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
2. **APPROVED/REJECTED:** The vendor (or admin) reviews the request.
3. **SHIPPED:** Buyer provides tracking info and ships it back.
4. **RECEIVED:** Vendor confirms receipt. Inventory is restocked. VendorOrder transitions.

## 4. Service Responsibilities
**`OrderService` additions (or new `ReturnService` within Orders):**
- `request_return(vendor_order_id, items: list[dict], reason)`: Validates items belong to `vendor_order`, order is `DELIVERED`.
- `approve_return(return_id)`: Transitions to `APPROVED`.
- `mark_return_received(return_id)`: Transitions to `RECEIVED`.
  - Triggers Inventory Restock.
  - Checks if all items in `VendorOrder` are returned. If so, updates `VendorOrder.status = RETURNED`.

**`InventoryService` updates:**
- `restock_inventory(variant_id, quantity)`: Modifies inventory stock physically upon return receipt.

## 5. Event Publication
Published via `EventBus` (Synchronous Domain Events where appropriate, or Integration Events for notifications):
- `ReturnRequestedEvent`
- `ReturnApprovedEvent`
- `ReturnReceivedEvent`

## 6. Business Rules & Validations
- Returns can only be initiated on `DELIVERED` VendorOrders.
- Total returned quantity per `OrderItem` across all returns cannot exceed `OrderItem.quantity`.
- Only `RECEIVED` returns restock inventory.

## 7. API Surface (Internal/System)
Internal domain service APIs (e.g., `ReturnService.request_return`) intended for future exposure to Buyer APIs and Admin APIs.
