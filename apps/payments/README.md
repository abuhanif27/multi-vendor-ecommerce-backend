# Payments Module

The `payments` module is the strict Anti-Corruption Layer (ACL) between external payment gateways (Stripe, bKash, SSLCommerz) and our internal domain.

## Core Responsibilities
1. Initialize secure payment intents.
2. Verify cryptographic webhooks.
3. Track financial ledgers (`Payment` model).
4. Alert `OrderService` exactly when an order transitions state based on financial guarantees.

## Architecture

This module utilizes a **Strategy Pattern** for gateways. All gateways (including Cash on Delivery) must inherit from `BaseGateway` to ensure a uniform API across the system.

### Financial Guarantee Rules (Idempotency)
External gateways are notoriously unreliable regarding network delivery. They may timeout, double-send webhooks, or drop packets.

To combat this, the `PaymentService` is strictly idempotent:
- It uses `.select_for_update()` to serialize concurrent webhooks.
- If a webhook says "CAPTURED" but our database already says "CAPTURED", we gracefully return `200 OK` and halt logic.
- We never touch the `Inventory` directly. If a payment succeeds, we notify `OrderService`, which handles downstream effects (like releasing or committing inventory locks).

## Endpoints

- **`POST /api/v1/payments/create/`**: Generates a provider checkout session for an authenticated user.
- **`POST /api/v1/payments/webhooks/stripe/`**: Unauthenticated receiver for Stripe. Verifies HMAC and processes logic.

## Adding a New Provider
1. Create `apps/payments/gateways/myprovider.py` inheriting from `BaseGateway`.
2. Implement `initialize_payment` and `verify_webhook`.
3. Add the provider to the `Payment.Provider` enum.
4. Route it inside `PaymentService._get_gateway()`.
