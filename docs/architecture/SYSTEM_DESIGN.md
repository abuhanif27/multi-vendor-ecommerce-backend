# System Design & Infrastructure Topology

This document outlines the infrastructure, database strategy, and caching topology required to operate the platform at scale.

## 1. Relational Persistence (PostgreSQL)
We rely entirely on PostgreSQL for transactional state.
- **UUID Primary Keys**: Every table uses UUIDv4 to prevent ID enumeration and ease distributed integrations.
- **Row-Level Locking**: `select_for_update()` is rigorously used in `InventoryService` and `PromotionService` to prevent concurrent race conditions during flash sales.
- **Database Constraints**: Integrity is pushed to the database (e.g., preventing duplicate usage of coupons via `UniqueConstraint`).

## 2. Distributed Caching (Redis)
Redis serves a dual purpose:
- **Broker**: Backing Celery queues.
- **Application Cache**: Caching heavy read operations (e.g., Catalog queries, Analytics Dashboard aggregations).
- **Invalidation Strategy**: We use Cache Versioning (`analytics_version_{shop_id}`). Instead of finding and deleting thousands of keys, we simply increment an integer version in Redis, which instantly orphans older cached dashboard segments.

## 3. Background Processing (Celery)
Celery operates entirely decoupled from the Django web threads.
- **celery-beat**: Runs scheduled CRON tasks.
  - Nightly `reconcile_daily_metrics` heals the Analytics rollup tables.
- **celery-workers**: Handle unpredictable, high-latency tasks:
  - Generating Vendor Sales CSVs.
  - Dispatching webhooks/emails.

## 4. Scalability Approach
- The Web Layer (Django/Gunicorn) is completely stateless (sessions are JWTs, no local memory stores). Thus, it can scale horizontally to infinite nodes behind an Nginx load balancer.
- PostgreSQL scale is handled via Vertical Scaling first, followed by read-replicas. Write-heavy tables (Analytics Rollups) are designed for future PostgreSQL native table-partitioning by date.
