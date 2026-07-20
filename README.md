# Core Commerce Platform

A production-grade, multi-vendor e-commerce backend built with Django, PostgreSQL, Redis, and Celery. 

## Overview
This platform acts as a headless API engine designed to support a scalable, high-throughput marketplace (e.g., Etsy, Shopify-lite). It enforces strict architectural boundaries using Domain-Driven Design (DDD) principles and a robust Service Layer, guaranteeing absolute separation of concerns between HTTP presentation, business logic, and background processing.

## Current Domains (v1.0.0-alpha)
The system is partitioned into 12 core domains:
- **Authentication**: JWT-based stateless auth for Buyers, Vendors, and Admins.
- **Catalog**: Products, Categories, Attributes, and Shop profiles.
- **Inventory**: Atomic, transactional inventory locking to prevent overselling.
- **Cart**: Stateful session tracking and line-item management.
- **Checkout**: A highly orchestrated, multi-step transaction pipeline ensuring ACID compliance across domains.
- **Orders**: Immutable order records with explicit state machines.
- **Payments**: Idempotent payment gateway integrations.
- **Shipping**: Provider-agnostic shipping calculations and tracking.
- **Notifications**: Event-driven Celery workers handling emails and webhooks.
- **Reviews & Reputation**: Aggregated scoring and moderation for Shops and Products.
- **Promotion Engine**: Mathematical evaluation strategies for Coupons and Stacking.
- **Vendor Dashboard & Analytics**: Fast, incremental atomic rollups for metric dashboards.

## Architecture Highlights
- **Thin Views**: DRF Views are strictly limited to request parsing and HTTP formatting.
- **Service Layer**: 100% of business logic resides in isolated, tested Service classes (`services.py`).
- **Typed Contracts**: Internal boundaries use Python `dataclasses` (DTOs) instead of raw dictionaries.
- **Event-Driven Side Effects**: Asynchronous work (analytics, emails, inventory deduction) is completely decoupled from hot HTTP paths via Domain Events.
- **Idempotency**: Critical paths (checkout, payments, analytics rollups) are built to survive concurrent requests, race conditions, and network retries.

## Documentation
- [Architecture & Request Lifecycle](docs/architecture/ARCHITECTURE.md)
- [System Design & Topology](docs/architecture/SYSTEM_DESIGN.md)
- [Development Guide](docs/engineering/DEVELOPMENT_GUIDE.md)
- [Contributing Standards](docs/engineering/CONTRIBUTING.md)
- [Architecture Decision Records (ADRs)](docs/adr/)
