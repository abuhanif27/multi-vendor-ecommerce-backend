# Product Moderation - Short Design

## Overview
Implement Product Moderation using the frozen Platform Foundation v1 administration patterns. This mirrors the Vendor Administration lifecycle to manage individual products submitted by vendors.

## 1. Product State Machine (Option A)
We utilize a single `ProductStatus` enum. The statuses are mutually exclusive in terms of visibility and actionability.
Allowed Transitions:
- `DRAFT` → `PENDING` (Vendor submits for review)
- `PENDING` → `ACTIVE` (Admin approves)
- `PENDING` → `REJECTED` (Admin rejects)
- `ACTIVE` → `SUSPENDED` (Admin suspends for violation)
- `SUSPENDED` → `ACTIVE` (Admin restores)
- `REJECTED` → `DRAFT` (Vendor edits and revises, preparing for resubmission)
- `ACTIVE` → `ARCHIVED` (Vendor deletes/archives)
- `SUSPENDED` → `ARCHIVED` (Vendor decides to discard)

*Note: The domain service strictly enforces `PENDING -> ACTIVE|REJECTED`, `ACTIVE -> SUSPENDED`, and `SUSPENDED -> ACTIVE`.*

## 2. Business Rules Validation
- **Can vendors edit rejected products?** Yes. Editing a rejected product transitions it back to `DRAFT` so the vendor can fix issues and resubmit.
- **Can vendors resubmit rejected products?** Yes, by transitioning it from `DRAFT` back to `PENDING`.
- **Can suspended products receive orders?** No. Suspended products act similarly to Drafts; they cannot be checked out.
- **Can suspended products appear in search?** No. Only `ACTIVE` products appear in the storefront.
- **Can archived products be restored?** No. `ARCHIVED` is a terminal state.
- **Does approving a product automatically make it visible?** Yes, it transitions to `ACTIVE`, making it globally visible immediately.

## 3. Consistency Review (vs Vendor Administration)
- **Permission Checks:** Uses `can_moderate_products` dynamically mirroring `can_approve_vendor`, etc.
- **Idempotency:** Implemented via `ProductService` mirroring `ShopService` (returning `Tuple[Product, bool]`).
- **Transaction Boundaries:** Enforced inside `ProductModerationService` using `transaction.atomic()`.
- **Audit Logging:** Logs generic actions `APPROVE`, `REJECT`, `SUSPEND`, `OTHER` identically to `AdminAuditLog.ACTION_CHOICES`.
- **Event Publication:** Uses `ProductApprovedEvent`, `ProductRejectedEvent` via `transaction.on_commit()`.
- **API Style:** REST endpoints map exactly to `Shop` endpoints (`/api/v1/admin/products/{id}/approve/`).
- **Exception Handling:** Centralized through `ValidationError` and `PermissionDenied`.

There are no deviations from the platform foundation patterns.

## 4. Domain Services
Create `ProductModerationService` in `apps.administration.services.product_moderation`.
- Methods: `approve_product`, `reject_product`, `suspend_product`, `restore_product`.

## 5. Event Publication
New integration events defined in `apps.administration.events`:
- `ProductApprovedEvent`
- `ProductRejectedEvent`
- `ProductSuspendedEvent`
- `ProductRestoredEvent`

These are strictly **Integration Events**, published on commit, for notifications or search indexing.

## 6. API Endpoints
`apps.administration.api.products`:
- `POST /api/v1/admin/products/{id}/approve/`
- `POST /api/v1/admin/products/{id}/reject/` (requires reason)
- `POST /api/v1/admin/products/{id}/suspend/` (requires reason)
- `POST /api/v1/admin/products/{id}/restore/` (requires reason)

## 6. Permissions and Auth
New Django permissions added to `apps.administration.models`:
- `can_approve_product`
- `can_reject_product`
- `can_suspend_product`
- `can_restore_product`
