# Release Candidate 2 (RC2) - Platform Audit

## Overview
This document represents a comprehensive architectural and operational audit of the Multi-Vendor E-Commerce Backend at the conclusion of Release Candidate 2 (RC2). It serves to evaluate the system as a cohesive whole rather than viewing individual capabilities in isolation.

## 1. Domain Dependency Graph

The platform follows a layered, domain-driven design structure. Dependencies flow strictly downward, avoiding circular loops.

- **Orchestration / Administration Domain** (`apps.administration`)
  - Depends on: All domains (for auditing and overriding)
- **Orders Domain** (`apps.orders`)
  - Depends on: `apps.cart`, `apps.inventory`, `apps.catalog`, `apps.payments`, `apps.shipping`
- **Payments Domain** (`apps.payments`)
  - Depends on: `apps.orders` (for order references), `apps.administration` (for audit)
- **Shipping Domain** (`apps.shipping`)
  - Depends on: `apps.orders`
- **Catalog & Inventory Domain** (`apps.catalog`, `apps.inventory`)
  - Depends on: `apps.shops` (Vendor isolation)
- **Core / Auth Domain** (`apps.accounts`, `apps.shops`)
  - Depends on: None

*Note: Integration between peer domains (e.g., Payments and Orders) is achieved primarily via the `EventBus` to preserve loose coupling.*

## 2. Event Publication & Subscription Graph

The `EventBus` (`apps.notifications.events.EventBus`) facilitates asynchronous and synchronous Domain and Integration events.

| Event | Publisher | Subscriber(s) | Type |
|-------|-----------|---------------|------|
| `OrderPlacedEvent` | `OrderService` | `PaymentService`, `InventoryService`, `NotificationService` | Domain |
| `PaymentCapturedEvent` | `PaymentService`| `OrderService` (mark paid), `NotificationService` | Domain |
| `PaymentRefundedEvent` | `PaymentService`| `OrderService` (adjust state), `ReturnService` | Domain |
| `ReturnReceivedEvent` | `ReturnService` | `InventoryService` (restock), `OrderService` | Domain |
| `DisputeOpenedEvent` | `DisputeService`| `NotificationService`, `Administration` | Domain |
| `DisputeResolvedEvent`| `DisputeService`| `PaymentService` (refund), `ReturnService` | Domain |
| `VendorSuspendedEvent`| `VendorService` | `CatalogService` (hide products), `Auth` | Domain |

## 3. Service Dependency Matrix

| Service | Acts As | Direct Collaborators (Synchronous) | Indirect Collaborators (Async/Events) |
|---------|---------|------------------------------------|---------------------------------------|
| `OrderService` | Orchestrator | `InventoryService`, `CartService` | `PaymentService`, `ShippingService` |
| `PaymentService` | Domain Core | `PaymentGatewayRegistry` | `OrderService`, `DisputeService` |
| `ReturnService` | Domain Core | `InventoryService` (sync) | `PaymentService`, `OrderService` |
| `DisputeService` | Orchestrator | `ReturnService`, `PaymentService` | `NotificationService` |
| `AuditService` | Cross-Cutting| All Domains | None |

## 4. Database Index Review

**Strengths:**
- Core foreign keys (`order_id`, `vendor_id`, `user_id`) are indexed by default in Django.
- Lookups on `status` fields across `Order`, `Payment`, `Return`, and `Dispute` are highly performant.
- `idempotency_key` fields on `Payment` and `Refund` are unique and implicitly indexed.

**Areas for Improvement (Technical Debt):**
- **Composite Indexes:** Missing composite indexes for frequent queries, e.g., `(vendor_id, status)` on `VendorOrder`.
- **Text Search:** Searching products by name/description currently relies on `icontains` (SQL `ILIKE`). This will degrade at scale without a Full-Text Search index (e.g., PostgreSQL `GinIndex` or external Elasticsearch).

## 5. Transaction Boundary Review

**Strengths:**
- The `@transaction.atomic` decorator is used effectively across all mutation operations (`process_webhook_success`, `resolve_dispute`, `mark_return_received`).
- Row-level locking (`select_for_update()`) is strictly enforced in:
  - `PaymentService.process_webhook_success`
  - `PaymentService.process_refund`
  - `ReturnService.mark_return_received`
  - `DisputeService.resolve_dispute`
- Idempotency checks are universally executed *inside* the locked transaction block.

**Weaknesses:**
- **External Calls in Transactions:** `PaymentService.process_refund` makes an HTTP call (`gateway.refund_payment()`) *inside* an atomic block. While currently acceptable for fast internal gateway APIs, this could cause prolonged DB locks if the SSLCommerz API times out (15s read timeout).

## 6. Security Checklist

- [x] **Authentication:** JWT is strictly enforced via `SimpleJWT`.
- [x] **Authorization:** Role-based access control (Admin, Vendor, Customer) is verified at the View/Service layer.
- [x] **Webhook Security:** SSLCommerz IPNs do not trust the payload; they trigger a backend validation check via `validationserverAPI.php`.
- [x] **Data Integrity:** Monetary calculations use `Decimal`. State transitions (e.g., `PENDING` -> `CAPTURED`) are strictly enforced.
- [x] **Secrets Management:** Environment variables are isolated (`.env`); no hardcoded credentials exist.

## 7. Performance Checklist

- [x] **N+1 Queries:** `select_related` and `prefetch_related` are used in high-traffic catalog APIs.
- [x] **Row Locking:** Scoped tightly to single rows (`select_for_update()` on aggregates).
- [ ] **Pagination:** Standardized via `DefaultPagination`, but deep pagination (offset-based) may slow down on very large tables. Keyset pagination (cursor) should be considered for RC3.
- [ ] **Caching:** No systematic Redis caching exists for heavily read models (e.g., `Category`, `Product` lists). 

## 8. Technical Debt Register

1. **HTTP Calls Inside DB Transactions:** Resolving refunds while holding a database lock poses a throughput risk. Needs an Outbox pattern or Saga for true asynchronous consistency.
2. **EventBus Implementation:** The current `EventBus` is synchronously routed in memory. If an event subscriber fails (e.g., `InventoryService.restock_inventory`), it rolls back the entire transaction. This tightly couples bounded contexts.
3. **Database Caching:** Missing caching layer for catalog reads.

## 9. Known Limitations

- **Dispute Workflows:** Currently, disputes map cleanly to Order/Payment lifecycles, but partial-order disputes (e.g., 1 item out of 5) are complex to mediate financially without splitting the `Payment` logic further.
- **Payment Gateways:** Only `COD` and `SSLCOMMERZ` are supported. Stripe/bKash require their own specific validations.

## 10. Future Roadmap (RC3)

The following architectural epics are proposed for Release Candidate 3 (RC3):

1. **Asynchronous Event Driven Architecture:** 
   - Migrate `EventBus` to Celery / RabbitMQ / Redis Streams.
   - Implement the Transactional Outbox pattern to decouple DB commits from message publication.
2. **Promotions & Discount Engine:**
   - Develop the Promotion Domain for coupons, flash sales, and cart-level discounts.
3. **Platform Configuration & Global Settings:**
   - Centralize platform settings (commission rates, fee structures, SLA timers) into a dynamic administration interface rather than static settings.
4. **Search Optimization:**
   - Implement PostgreSQL Full-Text Search or Elasticsearch for the Catalog domain.
