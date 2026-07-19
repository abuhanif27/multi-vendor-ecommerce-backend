# Checkout Module

The `checkout` module acts as the strict stateless orchestrator between the user's intent to buy (the `cart` module) and the final legal purchase record (the `orders` module). 

## Domain Boundaries

- **Stateless Design**: The checkout module contains NO models. It does not persist checkout sessions. State is computed dynamically from the `cart` and user inputs.
- **Validation**: It acts as the gatekeeper. It strictly validates inventory limits and catches real-time price fluctuations from vendors before allowing an order to proceed.
- **Isolation**: Checkout has absolutely no knowledge of payment providers (Stripe, PayPal) or order models. It merely prepares a standardized DTO (Data Transfer Object) payload.

## Core Components

### `CheckoutService`
Located in `services/checkout.py`.
Handles all business logic, removing logic entirely from Views and Serializers.

1. **`get_checkout_summary(user)`**:
   - Reads the user's active cart.
   - Dynamically calculates the `subtotal` based on the LIVE prices of the product variants (not the snapshot unit_price in the cart).
   - Validates live inventory levels (`quantity_on_hand` - `quantity_reserved`).
   - Surfaces `warnings` if a vendor changed a price while the item was sitting in the cart, or if the stock is insufficient.

2. **`process_checkout(user, shipping_address, billing_address=None)`**:
   - Re-runs `get_checkout_summary` to enforce that no warnings block the transaction.
   - Wrapped in `@transaction.atomic`.
   - Iterates through the cart items, calling `InventoryService.reserve_stock` (which holds database locks `select_for_update` to prevent race conditions).
   - If any item fails reservation (e.g. concurrent buyer took the last stock), the entire atomic block rolls back seamlessly. No manual release needed.
   - Transitions the Cart status to `CHECKED_OUT`.
   - Groups items by `shop_id` to support future Multi-Vendor Parent/Child Orders.
   - Returns a structured DTO payload.

## Order Handoff Payload (DTO)

When `CheckoutService.process_checkout` completes successfully, it returns a precise payload representing the financial and logical breakdown of the order.

```python
{
    "user": <User instance>,
    "shipping_address": {
        "street": "...",
        "city": "...",
        "state": "...",
        "postal_code": "...",
        "country": "..."
    },
    "billing_address": { ... },
    "cart_id": "UUID string",
    "financials": {
        "subtotal": Decimal('...'),
        "shipping_total": Decimal('0.00'),
        "tax_total": Decimal('0.00'),
        "grand_total": Decimal('...')
    },
    "vendor_orders": {
        "shop_uuid_1": {
            "vendor_subtotal": Decimal('...'),
            "items": [ <CartItem instance>, ... ]
        }
    }
}
```

## Inventory Integration
Checkout strictly handles **Reservation**. It loops over valid items and requests reservations.
It **NEVER** decreases physical stock permanently. Permanent stock deduction is the sole responsibility of the Payment webhook (converting a temporary reservation into a permanent deduction).
If payment times out or fails, a future scheduled job or webhook handler will call `InventoryService.release_stock()` utilizing the Order records.

## Query Optimization
To prevent N+1 queries, especially in carts containing dozens of distinct products, the `CheckoutService` utilizes:
```python
cart.items.select_related('variant__product__shop', 'variant__inventory').all()
```
This guarantees that all variant, product, shop, and inventory data is loaded into memory in a single SQL round-trip.
