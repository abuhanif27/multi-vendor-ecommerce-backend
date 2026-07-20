# ADR-002: Event-Driven Architecture (Domain Events)

## Context
In a distributed e-commerce platform, taking an action in one domain almost always requires reactions in other domains. For example, when an `Order` is placed, we must:
1. Deduct Inventory
2. Clear the Shopping Cart
3. Send a Confirmation Email
4. Update Analytics Rollups

## Problem
If the `CheckoutService` explicitly calls `EmailService.send()`, `AnalyticsService.increment()`, and `CartService.clear()`, the Checkout domain becomes hopelessly coupled to every other domain in the system.

## Decision
We utilize **Domain Events** as an in-process Pub/Sub Event Bus.
When an action completes, the originating Service emits a strongly typed event (e.g., `OrderCompletedEvent(order_id=..., total=...)`).
Other domains register *handlers* that listen for these events. The handlers dictate whether the reaction happens synchronously (like Analytics updates) or asynchronously via Celery (like Emails).

## Alternatives Considered
- **Direct Synchronous Calls**: Rejected due to tight coupling and violation of Domain boundaries.
- **Message Brokers (Kafka/RabbitMQ)**: Overkill for our current deployment footprint. We can achieve the same decoupling in Python using Django Signals or a lightweight event dispatcher, reserving Redis/Celery strictly for heavy background workers.

## Consequences
- **Pros**: Domains remain completely isolated. New reactions (like firing a Webhook) can be added simply by registering a new handler, without touching `CheckoutService`.
- **Cons**: It becomes harder to trace the exact chronological execution path of a request without tracing the event listeners.

## Trade-offs
We traded explicit code linearity for extreme loose coupling and extensibility.
