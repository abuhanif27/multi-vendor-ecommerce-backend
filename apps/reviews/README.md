# Reviews & Reputation Module

This module manages all customer feedback, including product reviews, shop/vendor reviews, and aggregate reputation metrics. It guarantees data integrity by deeply integrating with the Orders domain to enforce verified purchases.

## Architecture & Business Rules

1. **Verified Purchase Enforcement**: A buyer can *only* review an item or shop if they have a matching `OrderItem` or `VendorOrder` that has reached the `DELIVERED` status.
2. **Idempotency & Duplicate Prevention**: The system enforces exactly one review per purchased item via a `OneToOneField` mapping directly to the `OrderItem` or `VendorOrder`.
3. **Reputation Metrics (Denormalization)**: The source of truth for global product/shop ratings lives directly on the `Product` and `Shop` models (e.g. `average_rating`, `review_count`). This ensures fast reads for catalog listing pages without expensive SQL `AVG()` aggregations per request.

## Event Flow

The module heavily leverages an event-driven architecture to compute reputation asynchronously:
1. `ReviewService` executes core validation and saves the review within a `transaction.atomic()` block.
2. The service uses `transaction.on_commit()` to broadcast a typed `ProductReviewChangedEvent` or `ShopReviewChangedEvent`.
3. Event handlers catch this in `apps.reviews.events` and dispatch Celery tasks (`sync_product_rating_task` / `sync_shop_rating_task`).
4. The background workers execute a mathematically safe `AVG()` over published reviews and directly update the `Product` or `Shop` models.

## APIs

Endpoints (powered by `ProductReviewViewSet` and `ShopReviewViewSet`):

- `GET /api/v1/product-reviews/` (List / Filter / Order)
- `POST /api/v1/product-reviews/` (Create Review)
- `PATCH /api/v1/product-reviews/{id}/` (Update Review - automatically tags `is_edited=True`)
- `DELETE /api/v1/product-reviews/{id}/` (Delete Review)
- `POST /api/v1/product-reviews/{id}/report/` (Flag a review for moderation)

*(And equivalent endpoints for `/api/v1/shop-reviews/`)*

## Future Extensions
- **Media Uploads**: Client-side direct-to-S3 uploads or a generic media endpoint can populate the `ProductReviewMedia` and `ShopReviewMedia` models.
- **Admin Moderation Portal**: Build a React/Vue dashboard consuming the `ReviewReport` models to triage and hide abusive reviews (`status=HIDDEN`).
- **Helpful Votes**: Add a `ReviewVote` model allowing users to upvote or downvote reviews for optimal sorting.
