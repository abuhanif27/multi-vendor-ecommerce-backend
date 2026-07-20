# ADR-004: Promotion Strategy Engine

## Context
Promotions (Coupons, Flash Sales, Buy-One-Get-One) require complex mathematical rules. These rules must determine if a user's Cart is eligible, and how much money to deduct.

## Problem
If promotion math is hardcoded into models or views, adding a new type of promotion (e.g., "Free Shipping over $50") requires rewriting the core engine. Furthermore, checking if a coupon is valid *without* actually applying it requires duplicated logic.

## Decision
We implemented a strict separation between **Validation/Evaluation** and **Consumption**.
- **Strategy Pattern**: The Promotion Engine leverages dynamic condition and reward registries. Math is executed dynamically based on the promotion configuration.
- **Stateless Pipeline**: `PromotionService.evaluate_cart()` runs side-effect-free. It can be called 100 times a second to recalculate cart totals without hitting the database.
- **Consumption**: `PromotionService.consume_coupon()` is a strict mutator that acquires row-locks to decrement usage limits.

## Alternatives Considered
- **Hardcoded Promo Types**: Rejected due to inflexibility.
- **JSON Rules Engines**: Fully defining math in JSON payloads. Rejected because it is extremely difficult to debug; we prefer code-based Strategy classes.

## Consequences
- **Pros**: Adding a new promo type requires simply writing one new isolated python Strategy class and registering it. 
- **Cons**: The abstraction introduces a learning curve for engineers used to simple CRUD promotions.

## Trade-offs
We traded code simplicity for dynamic, scalable, multi-layered discount resolution.
