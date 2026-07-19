# Order Module

The `orders` module is the immutable ledger of the application. It receives validated intent from the `checkout` module and turns it into permanent financial and fulfillment records.

## Architecture

This module utilizes a **Parent/Child** architecture to seamlessly support multi-vendor transactions from a single buyer checkout.

1. **`Order` (Parent)**: Belongs to the buyer. Holds the total financial aggregates (grand total, total tax, etc.) and the immutable JSON snapshots of the shipping and billing addresses.
2. **`VendorOrder` (Child)**: Belongs to a specific Vendor's `Shop`. It isolates the exact portion of the order that a specific vendor needs to fulfill, allowing vendors to manage their fulfillment independently without seeing competitors' items.
3. **`OrderItem` (Snapshot)**: The actual items purchased. It stores hard snapshots of the `product_name`, `sku`, `unit_price`, and `image_url`. Even if the vendor deletes or alters the product months later, the invoice remains 100% accurate.

## State Machines

- **Order Status**: Tracks financial progress (e.g., `PENDING`, `PAID`, `FAILED`).
- **VendorOrder Status**: Tracks fulfillment progress (e.g., `PENDING`, `PROCESSING`, `SHIPPED`).

## Integration with Inventory

The `orders` module strictly integrates with the `inventory` module to manage physical stock:
- **Reservation**: Handled upstream during `CheckoutService`.
- **Cancellation**: If `OrderService.cancel_order()` is invoked (due to a buyer cancellation or a payment timeout), the service automatically iterates through all items and calls `InventoryService.release_stock()` to return the stock to the market.
- **Commit**: (Future Phase) When a Payment webhook marks an order as `PAID`, `InventoryService.commit_stock()` will be invoked to permanently deduct the physical `quantity_on_hand`.

## APIs & Permissions

- **Buyer APIs**: `GET /api/v1/orders/` allows buyers to view their complete nested orders.
- **Vendor APIs**: `GET /api/v1/vendor-orders/` allows vendors to strictly see and manage the subsets of orders that belong to their shops.
- Both use robust `prefetch_related` queryset optimizations to completely eliminate N+1 queries during serialization.
