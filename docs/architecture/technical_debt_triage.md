# Technical Debt Triage

## Overview
This document categorizes and prioritizes the architectural and operational items identified in the RC2 Platform Audit. The objective is to establish an actionable engineering roadmap for resolving technical debt based on severity and risk, rather than simply cataloging it.

## Classification System
- **P0**: Must be resolved before production launch.
- **P1**: Should be resolved before large-scale traffic.
- **P2**: Improvement for RC3.
- **P3**: Nice to have.

---

## 1. HTTP Calls Inside DB Transactions (Refund API)
Currently, `PaymentService.process_refund()` executes an outbound HTTP request to the SSLCommerz Refund API (`gateway.refund_payment()`) while holding a row-level database lock via `select_for_update()`. 

- **Classification:** **P0** (Must resolve before production)
- **Impact:** High. If the gateway server takes 15 seconds to respond or time out, the database row (and potentially table pages) remains locked for 15 seconds. Concurrent requests or queries trying to read/update that transaction will block, starving the database connection pool.
- **Risk:** High risk of connection pool exhaustion and database deadlock during API degradation.
- **Estimated Implementation Complexity:** Medium. Requires decoupling the state transition from the API call, potentially using a simple asynchronous task (Celery) or a 2-phase commit logic.
- **Recommended Milestone:** **Pre-Production (Stabilization Sprint)**

---

## 2. EventBus Synchronous Routing
The current `EventBus` (`apps.notifications.events.EventBus`) routes events synchronously in-memory. If a non-critical subscriber (e.g., Analytics) fails while processing an event, the exception bubbles up and rolls back the core domain's transaction (e.g., `OrderService`).

- **Classification:** **P1** (Should resolve before large-scale traffic)
- **Impact:** High. Tightly couples domains and reduces system resiliency. The failure of a downstream notification or inventory restock can cause checkout/payment webhooks to fail.
- **Risk:** High operational risk of cascading failures.
- **Estimated Implementation Complexity:** High. Requires migrating the EventBus to an asynchronous message broker (e.g., Celery/RabbitMQ) and potentially implementing the Transactional Outbox pattern.
- **Recommended Milestone:** **RC3 (Core Infrastructure Epic)**

---

## 3. Database Caching for Catalog Reads
High-traffic endpoints (Product Listing, Category Listing) hit the database directly for every read. No Redis/Memcached layer exists for these frequently accessed, rarely mutated models.

- **Classification:** **P1** (Should resolve before large-scale traffic)
- **Impact:** Medium-High. Without caching, the database will become the immediate bottleneck during traffic spikes or flash sales.
- **Risk:** Low risk to data integrity, high risk to availability during load.
- **Estimated Implementation Complexity:** Low-Medium. Implementation of standard Django caching (Redis) for DRF `ListAPIView` endpoints and cache invalidation signals on `Product` mutations.
- **Recommended Milestone:** **RC3 (Performance Epic)**

---

## 4. Text Search using SQL `icontains`
Product searches currently rely on Django's `icontains`, which compiles to `ILIKE '%query%'` in SQL, causing full table scans.

- **Classification:** **P1** (Should resolve before large-scale traffic)
- **Impact:** Medium. Performance will degrade linearly as the catalog grows.
- **Risk:** Medium risk of slow query timeouts.
- **Estimated Implementation Complexity:** Medium. Migration to PostgreSQL `GinIndex` with `SearchVector` or integration with an external search engine like Elasticsearch/Typesense.
- **Recommended Milestone:** **RC3 (Search Engine Epic)**

---

## 5. Missing Composite Indexes
Frequent read patterns, such as filtering `VendorOrder` by `(vendor_id, status)`, lack composite database indices.

- **Classification:** **P2** (Improvement for RC3)
- **Impact:** Medium. Leads to sequential scans on specific vendor dashboards as their order volume grows.
- **Risk:** Low. Will not break the system, merely slows down dashboard load times for large vendors.
- **Estimated Implementation Complexity:** Low. Can be resolved by adding `models.Index` arrays in the `Meta` class of models and generating a migration.
- **Recommended Milestone:** **RC3 (Maintenance Sprint)**

---

## 6. Offset-Based Pagination
The API relies on standard `DefaultPagination` (offset/limit). Deep pagination (e.g., `?page=5000`) forces the database to fetch and discard thousands of rows.

- **Classification:** **P2** (Improvement for RC3)
- **Impact:** Low-Medium. Only affects users who page deeply into result sets.
- **Risk:** Low.
- **Estimated Implementation Complexity:** Medium. Requires transitioning DRF endpoints to Cursor-based (Keyset) pagination.
- **Recommended Milestone:** **RC3 (Performance Epic)**

---

## 7. Partial-Order Dispute Abstraction
Dispute orchestration handles full orders easily, but the logic to mediate financial refunds for 1 item out of a 5-item order is tightly coupled and lacks a dedicated financial split calculation engine.

- **Classification:** **P3** (Nice to have)
- **Impact:** Low. Partial disputes are less frequent and can currently be mediated via manual Admin overrides.
- **Risk:** Low. 
- **Estimated Implementation Complexity:** High. Requires restructuring the `Payment` aggregate to support partial allocations natively.
- **Recommended Milestone:** **Future (Post-RC3)**
