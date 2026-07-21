# Product Moderation - Short Design

## Overview
Implement Product Moderation using the frozen Platform Foundation v1 administration patterns. This mirrors the Vendor Administration lifecycle to manage individual products submitted by vendors.

## 1. Business Rules
- **Statuses Required:** Extend `Product.ProductStatus` to include `PENDING`, `REJECTED`, and `SUSPENDED`.
- **Transitions:**
  - `DRAFT` → `PENDING`: Vendor submits product for review.
  - `PENDING` → `ACTIVE` (Approval)
  - `PENDING` → `REJECTED` (Rejection)
  - `ACTIVE` → `SUSPENDED` (Admin suspension)
  - `SUSPENDED` → `ACTIVE` (Admin restoration)
- **Visibility:** Only `ACTIVE` products are visible to customers. Suspended or Rejected products can only be accessed by the owning Vendor and platform Administrators.

## 2. Domain Services
Create `ProductModerationService` in `apps.administration.services.product_moderation`.
- Methods: `approve_product`, `reject_product`, `suspend_product`, `restore_product`.
- These will orchestrate updates via `CatalogService` or `ShopService` (depending on where the status lives), following the exact canonical pattern used in `VendorService`.

## 3. Canonical Administration Workflow
Each domain service method will strictly enforce the canonical workflow:
1. **Permission Check:** Verify `actor.has_perm('administration.can_approve_product')` etc.
2. **Idempotency Check:** Avoid duplicate processing if already in the target state.
3. **`transaction.atomic()`:** Wrap the state change and audit log.
4. **Audit Logging:** `AuditService.log_action` (e.g., `PRODUCT_APPROVED`, `PRODUCT_SUSPENDED` with reasons).
5. **Event Publication:** `transaction.on_commit(lambda: EventBus.publish(IntegrationEvent))`

## 4. Event Publication
New integration events defined in `apps.administration.events`:
- `ProductApprovedEvent`
- `ProductRejectedEvent`
- `ProductSuspendedEvent`
- `ProductRestoredEvent`

These are strictly **Integration Events**, published on commit, for notifications or search indexing.

## 5. API Endpoints
Create `apps.administration.views.product_moderation`:
- `POST /api/admin/products/{id}/approve/`
- `POST /api/admin/products/{id}/reject/` (requires reason)
- `POST /api/admin/products/{id}/suspend/` (requires reason)
- `POST /api/admin/products/{id}/restore/` (requires reason)
- Access governed by `IsAdminUser` and specific view-level permissions.

## 6. Permissions and Auth
New Django permissions added to `apps.administration.models`:
- `can_approve_product`
- `can_reject_product`
- `can_suspend_product`
- `can_restore_product`
