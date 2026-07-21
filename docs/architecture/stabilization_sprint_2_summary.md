# Stabilization Sprint 2 - Implementation Summary

## Phase 1: Architectural Correctness
- **Removed Serializer Status Mutations**: Removed `VendorOrderUpdateSerializer` from `VendorOrderDetailView`. Vendors can no longer mutate the `status` of an order arbitrarily via REST primitives. State transitions are now strictly orchestrated.
- **Removed Circular Dependencies**: Removed the direct import of `OrderService` from `ShippingService`. The `update_shipment_status` method now triggers a `ShipmentDeliveredEvent` via the `EventBus`, resolving the architectural bypass.
- **Event Subscriptions**: Configured `apps.orders.apps` to cleanly subscribe to `ShipmentDeliveredEvent` on application load.

## Phase 2: Database Hardening
- **Missing Indexes**: Added `db_index=True` to the highly-filtered `status` fields on `Shop`, `Product`, `Order`, and `VendorOrder`.
- **Unique Constraints (Vendor Orders)**: Implemented `models.UniqueConstraint(fields=['order', 'shop'])` to prevent duplication of sub-orders on accidental double checkouts.
- **Unique Constraints (Images)**: Added conditional `UniqueConstraint` on `ProductImage` and `VariantImage` enforcing that only ONE image can be marked `is_primary=True` for a given product or variant.
- **Migrations Generated**: Generated and applied `shops.0013_...` and `orders.0003_...`.

## Phase 3: Performance
- **Fixed N+1 Queries**: Appended `.select_related('vendor_order__shop')` to `VendorShipmentDetailAPIView`, `VendorShipmentAssignCourierAPIView`, and `VendorShipmentStatusUpdateAPIView` base querysets. This eliminates N+1 database hits during Django REST Framework's object-level permission evaluation (`IsVendor`).

## Phase 4: Transaction Review
- **Event Bus Transaction Boundary**: Re-evaluated `transaction.on_commit` usage in internal EventBus publishing. Internal choreography (e.g. `Shipment` triggering `Order` completion) is now executed synchronously inside the same `transaction.atomic()` block. This guarantees atomicity: if the `Order` update fails, the `Shipment` status rolls back, preventing distributed inconsistencies. (External I/O such as emails will continue to use `on_commit`).

## Phase 5: Verification
- **Test Execution**: The complete test suite for `apps.orders`, `apps.shops`, and `apps.shipping` (29 explicit integration tests) passed flawlessly after all architectural fixes, constraint modifications, and EventBus updates.

Status: All critical and high findings from the Engineering Health Report have been resolved. The system is hardened and ready for the next set of business capabilities.
