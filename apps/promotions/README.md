# Promotion Engine

The Promotion Engine domain acts as the definitive source of truth for all pricing reductions across the marketplace. It evaluates customer carts against active campaigns and user-supplied codes to return a structured Pricing Contract.

## Architecture

1. **Service Layer Hegemony**: All logic is strictly encapsulated within `PromotionService` (evaluation orchestration) and `PromotionEngine` (mathematical calculation strategies).
2. **Read vs Write Isolation**:
   - `evaluate_cart()`: Completely side-effect free. Can be called hundreds of times per second (e.g., live cart updates).
   - `consume_coupon()`: Heavily guarded mutation. Called *exactly once* during Checkout's `transaction.atomic()` block.
3. **Data Integrity via Row Locks**: During `consume_coupon()`, `Coupon.objects.select_for_update()` is applied to serialize access to the coupon, strictly averting race-condition concurrency bypasses on `max_uses`.

## Strategy Engine

The engine relies on a modular Strategy Pattern mapped to enums to allow infinite extensibility without modifying the orchestration logic:
- **Condition Evaluators** (`MinSubtotalEvaluator`, `SpecificCategoryEvaluator`, etc.): Defines rules for eligibility.
- **Reward Calculators** (`PercentageCalculator`, `FixedAmountCalculator`, `FreeShippingCalculator`): Calculates the explicit markdown value.

## DTO Contracts

Checkout and Promotions communicate solely via rigidly defined DTOs:
- **Inbound (`CheckoutContextDTO`)**: Subtotal, user context, line items, and active coupon codes.
- **Outbound (`PromotionEvaluationResult`)**: Contains a deeply structured `PricingBreakdownDTO`, alongside detailed arrays of `applied_promotions` (for receipt logging) and explicit `CouponRejectionDTO`s (for frontend UI warnings).

## Event Flow

- **`CouponUsageRecordedEvent`**: Published safely `on_commit` when a coupon is successfully bound to a placed order.
- **`PromotionExhaustedEvent`**: Published when `current_uses` meets `max_uses` inside the lock, triggering downstream alerts (e.g., notifying the vendor their campaign finished).

## Business Rules & Conflict Resolution
- **Stacking Engine**: Automatically prioritizes campaigns by `priority` (descending). If an `is_exclusive` campaign triggers, all subsequent validations are immediately halted.
- **Deterministic Evaluation**: Tie-breakers are resolved using the UUID to guarantee identical inputs always produce identical output prices.
- **Multi-Tenant Boundaries**: Vendors can only bind promotions to their own `shop_id`. An automatic promotion missing a `shop_id` is a global marketplace campaign managed strictly by administrators.

## API Endpoints
- **Public**: `POST /api/v1/promotions/validate/` (Rate Limited 10/min)
- **Management**: `CRUD /api/v1/admin/promotions/` (Protected by `IsVendorOwnerOrAdmin`)
