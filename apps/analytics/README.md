# Vendor Dashboard & Analytics

The Analytics domain acts as an aggregation and reporting overlay. It possesses **no authority over business logic**. Its sole responsibility is to ingest data and events from across the platform and project them into high-performance analytical views.

## Architecture

1. **Event-Driven Rollups**: `ShopMetricRollup` and `ProductVelocityRollup` are updated lock-free via `transaction.atomic()` increments using `F()` expressions when transactional domain events (`OrderCompletedEvent`) fire.
2. **Separation of Concerns**: 
    - `AnalyticsService`: Sole owner of querying raw facts and producing derived mathematical KPIs (`AOV`, `cancellation_rate`, `return_rate`).
    - `ReportingService`: Sole owner of heavy IO background exports (e.g. `CSV` generation).
3. **Data Integrity boundaries**: The models enforce temporal integrity via `period_start` and `period_end` DateFields, constrained via database-level `UniqueConstraint`.

## Caching Strategy
- The API explicitly supports high-frequency Dashboard renders by returning abstract `WidgetDataDTO` representations alongside explicit structural KPIs (`SalesSummaryDTO`).
- Fast invalidation occurs using a versioned Redis Key (`analytics_version_{shop_id}`). The frontend/view layer can use this to hold dashboard responses in cache indefinitely until a new live order triggers a cache version bump from `AnalyticsService.increment_shop_metrics()`.

## API Endpoints
- `GET /api/v1/analytics/dashboard/`
- `POST /api/v1/analytics/export-sales/`

Both endpoints are protected by `IsAnalyticsViewer`. Vendors are inherently locked to their own Shop. Marketplace Administrators can request any `shop_id`, or `null` to view the entire global multi-vendor ecosystem's aggregated performance.
