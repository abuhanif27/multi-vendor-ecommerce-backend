# Review Moderation - Short Design

## Overview
Implement Review Moderation for both Product Reviews and Shop Reviews utilizing the frozen Platform Foundation v1 administration patterns. This enables platform administrators to handle user reports and enforce community guidelines.

## 1. Review State Machine
The `ReviewStatus` enum contains only strict moderation outcomes: `PUBLISHED`, `HIDDEN`, `REMOVED`.

The reporting workflow (`FLAGGED`) is separated from the moderation state. User reports accumulate in `ProductReviewReport` or `ShopReviewReport`. The review itself retains its structural moderation state (e.g., `PUBLISHED`) regardless of how many open reports exist, unless thresholds automatically hide it or an administrator takes action.

Allowed Moderation Transitions:
- `PUBLISHED` → `HIDDEN` (Admin hides the review temporarily pending investigation)
- `PUBLISHED` | `HIDDEN` → `REMOVED` (Admin permanently removes the review for violating guidelines)
- `HIDDEN` → `PUBLISHED` (Admin restores the review)

## 2. Business Rules Validation
- **Visibility:** Only `PUBLISHED` reviews are visible on the storefront.
- **Reporting:** When a review is reported, the report is logged in `ProductReviewReport` or `ShopReviewReport`. The review status does not change automatically.
- **Resolution:** When an admin modifies the state of a review (e.g., restores, hides, or removes it), all pending `ProductReviewReport` / `ShopReviewReport` objects associated with that review should be atomically marked `is_resolved = True` in the same transaction.

## 3. Domain Services
Create `ReviewModerationService` in `apps.administration.services.review_moderation`.
- Methods for Product Reviews: `hide_product_review`, `remove_product_review`, `restore_product_review`.
- Methods for Shop Reviews: `hide_shop_review`, `remove_shop_review`, `restore_shop_review`.
- Underlying mutators will be placed in `apps.reviews.services.review_management.py`.

## 4. Canonical Administration Workflow
Each domain service method enforces the canonical workflow:
1. **Permission Check:** Verify `actor.has_perm('administration.can_moderate_reviews')`.
2. **Idempotency Check:** Skip execution if the review is already in the target state.
3. **`transaction.atomic()`:** Wrap the state change, resolving of reports, and audit log.
4. **Audit Logging:** `AuditService.log_action` (using `UPDATE` or `OTHER`, specifying state change in payload since specific review enums don't exist in `ACTION_CHOICES`).
5. **Event Publication:** Publish Integration Events via `EventBus`.

## 5. Event Publication
New integration events in `apps.administration.events`:
- `ProductReviewModeratedEvent`
- `ShopReviewModeratedEvent`
Both will contain `review_id`, `actor_id`, `new_status`, and `reason`.

## 6. API Endpoints
`apps.administration.api.reviews`:
- `POST /api/v1/admin/reviews/product/{id}/hide/`
- `POST /api/v1/admin/reviews/product/{id}/remove/`
- `POST /api/v1/admin/reviews/product/{id}/restore/`
- `POST /api/v1/admin/reviews/shop/{id}/hide/`
- `POST /api/v1/admin/reviews/shop/{id}/remove/`
- `POST /api/v1/admin/reviews/shop/{id}/restore/`
