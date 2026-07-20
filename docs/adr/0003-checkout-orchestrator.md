# ADR-003: Checkout Orchestrator

## Context
Checkout is the most critical operation in the platform. A customer submits a cart containing multiple products. The system must verify prices, validate coupon conditions, acquire row-level locks on inventory, charge the credit card, and persist the Order.

## Problem
If this pipeline breaks halfway through (e.g., the credit card declines *after* inventory is locked, or the database crashes *after* the card is charged), the system enters a corrupted state (phantom inventory, lost money).

## Decision
We utilize the **Orchestrator Pattern** wrapped entirely within a monolithic PostgreSQL `transaction.atomic()` block.
The `CheckoutService` acts as the orchestrator. It executes a strict, ordered pipeline:
1. Dry-run Promotions
2. Lock Inventory (`select_for_update()`)
3. Execute Payment Gateway Authorization
4. Persist Order
5. Persist Coupon Usages
6. Commit Database Transaction

If the payment gateway fails, an exception is raised, and PostgreSQL automatically rolls back the inventory locks.

## Alternatives Considered
- **Choreography (Saga Pattern)**: Having each service emit an event and the next service reacting. Rejected because distributed rollback logic (compensating transactions) is incredibly difficult to build and test. Given we are currently on a single physical Postgres instance, a monolithic database transaction is far superior.

## Consequences
- **Pros**: Absolute ACID guarantees. It is impossible to generate phantom orders or leak inventory.
- **Cons**: The database transaction is held open during the Payment Gateway network request. If the gateway is slow, it holds row locks on inventory, reducing theoretical max throughput.

## Trade-offs
We traded ultra-high concurrent throughput (which requires eventual consistency) for absolute mathematical correctness (ACID).
