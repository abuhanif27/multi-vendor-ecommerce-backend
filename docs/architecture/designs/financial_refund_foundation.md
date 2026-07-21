# Phase 1: Financial Refund Foundation Design

## 1. Objective
Establish a robust financial ledger and orchestration layer to process full and partial refunds for multi-vendor orders, independent of return logistics or dispute moderation.

## 2. Domain Model
Introduce a `Refund` model in the Payments domain to track individual refund transactions against a parent `Payment`.

```python
class RefundStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending Gateway Processing'
    SUCCEEDED = 'SUCCEEDED', 'Refund Succeeded'
    FAILED = 'FAILED', 'Refund Failed'

class Refund(UUIDModel, TimeStampedModel):
    payment = models.ForeignKey('Payment', on_delete=models.PROTECT, related_name='refunds')
    vendor_order = models.ForeignKey('orders.VendorOrder', on_delete=models.SET_NULL, null=True, blank=True)
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    
    status = models.CharField(max_length=20, choices=RefundStatus.choices, default=RefundStatus.PENDING)
    
    provider_reference = models.CharField(max_length=255, blank=True)
    idempotency_key = models.UUIDField(unique=True)
    
    raw_metadata = models.JSONField(default=dict, blank=True)
```

## 3. Refund Lifecycle (State Machine)
1. **PENDING:** Refund requested; API call dispatched to external gateway (e.g., Stripe).
2. **SUCCEEDED:** Gateway confirms refund. Payment's overall refunded status is evaluated.
3. **FAILED:** Gateway rejects refund.

## 4. Service Responsibilities
**`PaymentService` additions:**
- `process_refund(payment_id: str, amount: Decimal, reason: str, vendor_order_id: str = None) -> Refund`: 
  - Verifies amount does not exceed `(payment.amount - SUM(successful_refunds))`.
  - Creates `Refund` record in `PENDING` state.
  - Calls `gateway.refund_payment()`.
  - Transitions to `SUCCEEDED` or `FAILED` synchronously (or via webhook if async).
  - Emits Integration Event on success.

**`OrderService` updates:**
- Subscribes to Refund events (or called synchronously if preferred) to update `Order.status` and `VendorOrder.status` to `REFUNDED` or `PARTIALLY_REFUNDED`.

## 5. Event Publication
Published via `EventBus` inside `transaction.on_commit()`:
- `PaymentRefundedEvent`: Payload includes `refund_id`, `payment_id`, `vendor_order_id`, `amount`, `status`.

## 6. Business Rules & Validations
- **Idempotency:** Unique `idempotency_key` guarantees no double refunds.
- **Validation:** Total sum of `SUCCEEDED` and `PENDING` refunds cannot exceed the original `Payment.amount`.
- **Eligibility:** Refunds can only be processed against `CAPTURED` payments.
- **Audit:** Any refund execution must be logged via `AuditService`.

## 7. API Surface (Internal/System)
This phase introduces internal domain service APIs rather than public REST endpoints. Future phases (Disputes) will expose REST endpoints that utilize these services.
- `PaymentService.process_refund(...)`
