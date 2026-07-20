# ADR-005: Analytics Incremental Rollups

## Context
Vendors require real-time dashboards to view their daily, monthly, and all-time sales metrics, as well as their top-performing products.

## Problem
In a multi-vendor marketplace, executing real-time `SUM(gross_total)` and `COUNT(id)` queries directly against millions of rows in the `Order` table will cause severe database degradation.

## Decision
We implemented an **Incremental Rollup Strategy**.
1. **Fact Tables**: We created `ShopMetricRollup` and `ProductVelocityRollup` tables keyed strictly by `shop_id`, `period_start`, and `period_end`.
2. **Atomic Increments**: When an `OrderCompletedEvent` fires, the `AnalyticsService` issues a lock-free PostgreSQL atomic update: `.update(gross=F('gross') + amount)`.
3. **Nightly Healing**: To guarantee mathematical perfection against potential event drops/duplicates, a Celery Beat task runs at 2:00 AM to perform a heavy aggregate scan of yesterday's `Order` table and explicitly overwrites yesterday's rollup row.

## Alternatives Considered
- **Real-time Aggregation**: Rejected because it cannot scale past tens of thousands of orders.
- **Data Warehousing (Snowflake/Redshift)**: Overkill for our current architecture. We want to keep everything within our single PostgreSQL cluster for operational simplicity.
- **Materialized Views**: PostgreSQL materialized views cannot be updated incrementally; they must be fully refreshed, which takes too long during business hours.

## Consequences
- **Pros**: The DRF View endpoints return complex dashboard data in milliseconds, regardless of how many millions of orders the platform processes.
- **Cons**: The real-time metric is technically eventually consistent and vulnerable to double-counting in edge-case network retries, relying on the nightly cron to fix anomalies.

## Trade-offs
We traded absolute real-time mathematical perfection for sub-millisecond read latency.
