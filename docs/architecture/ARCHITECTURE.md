# System Architecture

This document defines the high-level boundaries, domain structure, and request lifecycles of the Core Commerce Platform.

## 1. Domain-Driven Design (DDD) Approach
The platform is organized by bounded contexts (Django apps) rather than technical concerns. Each domain is self-contained. 
- `apps/catalog` knows nothing about `apps/orders`.
- To communicate, domains use **DTOs** (Data Transfer Objects) and **Service Layer** methods.

## 2. Request Lifecycle
We strictly forbid "Fat Models" and "Fat Views". The lifecycle of a request must flow downward through strict tiers:

1. **View / ViewSet** (`views.py`)
   - Authenticates and authorizes.
   - Parses HTTP inputs using DRF Serializers.
   - Calls the relevant Service(s).
   - Translates Service responses/DTOs back to HTTP Status codes.
   
2. **Service Layer** (`services.py`)
   - The absolute core.
   - Evaluates business rules.
   - Manages database mutations and `transaction.atomic()` boundaries.
   - Emits Domain Events.
   
3. **Data Access (Models)** (`models.py`)
   - Pure persistence.
   - Uses Django ORM.
   - Employs strict relationships and constraints (e.g., CheckConstraints, UniqueConstraints).
   
4. **Event Handlers** (`events.py`)
   - Listens to Domain Events.
   - Enqueues Celery Tasks or executes out-of-band updates (like Analytics).

## 3. Asynchronous Boundaries
Tasks that do not need to block the HTTP response are deferred.
- **Email/SMS**: Offloaded to Celery.
- **Analytics**: Rollup counters are incremented in-band using fast atomic `F()` expressions, but the CSV generation is deferred to Celery `ReportingService`.
- **Payment Verification**: Synchronous for checkout, but asynchronous for webhook reconciliations.

## 4. The Orchestrator Pattern
In highly complex mutations (like Checkout), a single `CheckoutService` acts as an Orchestrator. It imports `InventoryService`, `PromotionService`, and `PaymentService`, executing them sequentially within a single `transaction.atomic()` block. If any step fails, the entire transaction rolls back cleanly, avoiding phantom orders or lost inventory.

## System Diagram
See the [Checkout Architecture Diagram](diagrams/checkout_flow.mmd) for a visual representation.
