# Engineering Health Report (Stabilization Sprint 2)

## Phase 1: Test Quality
- **Total Tests**: 137 tests discovered and passing.
- **Breakdown**: The suite is reasonably split between Unit tests (Services/Models) and API/Integration tests (Views/Endpoints). Concurrency testing is simulated via E2E logic due to SQLite thread constraints.
- **Weakly Tested Modules**: `apps/common` (mixins, pagination) and `apps/api` (top-level routing) do not have explicit coverage footprints compared to the dense business domains (`administration`, `shops`, `orders`).

## Phase 2: Database Review
**[High] Missing Indexes on Status Fields**
- **Evidence**: `status` fields in `Shop`, `Product`, `Order`, and `VendorOrder` are standard `CharField`s without `db_index=True`.
- **Impact**: Queries like `Shop.objects.filter(status='approved')` will trigger full table scans as the dataset grows.

**[High] Missing Unique Constraint on Vendor Orders**
- **Evidence**: `VendorOrder` lacks a `unique_together = ['order', 'shop']` constraint.
- **Impact**: If a checkout bug occurs, duplicate sub-orders for the same vendor could be generated within a single user checkout session.

**[Medium] Missing Unique Constraints on Primary Images**
- **Evidence**: `ProductImage` and `VariantImage` lack a unique constraint on `['product', 'is_primary']` / `['variant', 'is_primary']`.
- **Impact**: It is possible for a single product to have multiple primary images if race conditions occur.

## Phase 3: Security Review
**[High] Bypass of Core Business Orchestration (Mass Assignment Risk)**
- **Evidence**: `VendorOrderUpdateSerializer` allows direct mutation of `VendorOrder.status` via a generic `VendorOrderDetailView(RetrieveUpdateAPIView)`.
- **Impact**: This entirely bypasses `transaction.atomic()`, Domain Events, Observability logs, and Audit logging designed in the orchestration layer (Services). Serializers should not directly advance complex state machines.

**[Medium] Inefficient IDOR Checks**
- **Evidence**: `VendorShipmentDetailAPIView` and related Shipping views manually check `if shipment.vendor_order.shop.owner != request.user` but the queryset (`Shipment.objects.all()`) lacks `select_related('vendor_order__shop')`.
- **Impact**: This executes N+1 database queries purely to authorize the request.

## Phase 4: Performance Review
**[Medium] Unused Base QuerySets**
- **Evidence**: `InventoryDetailAPIView` declares `queryset = Inventory.objects.all()` but the object retrieval is entirely hijacked by `InventoryLookupMixin.get_object()`.
- **Impact**: Confusing developer experience, though DRF doesn't execute the raw queryset.

## Phase 5: Code Quality
**[High] Domain Coupling & Event Architecture Bypass**
- **Evidence**: `apps/shipping/services/shipping.py` inside `update_shipment_status()` imports `OrderService` directly and calls `OrderService.mark_vendor_order_delivered(shipment.vendor_order.id)`. 
- **Impact**: This tightly couples Shipping to Orders (creating circular dependency risks) and violates the EventBus architecture. The Shipping service should emit a `ShipmentDeliveredEvent` which the Orders domain listens to.

## Phase 6: Documentation
**[Medium] Missing Technical ADRs**
- **Evidence**: The project lacks an ADR explicitly forbidding Serializer-level model mutations for entities governed by Finite State Machines (FSM). 

---

### Implementation Recommendations
For the immediate stabilization sprint, the following must be fixed:
1. Add `db_index=True` to all `status` CharFields.
2. Add `unique_together = ['order', 'shop']` to `VendorOrder`.
3. Refactor `VendorOrderUpdateSerializer` / View to delegate strictly to an `OrderService.update_vendor_order_status()` orchestrator.
4. Refactor `ShippingService` to emit `ShipmentDeliveredEvent` rather than directly importing `OrderService`.
5. Add `select_related('vendor_order__shop')` to Shipping API View querysets to eliminate N+1 auth queries.
