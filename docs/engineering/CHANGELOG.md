# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0-alpha] - 2026-07-21
### Added
- **Authentication**: JWT stateless authentication strategy for diverse user roles.
- **Catalog**: Core product and vendor shop definitions.
- **Inventory**: Highly concurrent `select_for_update()` transaction locking logic.
- **Cart**: Stateful shopping cart pipelines.
- **Checkout**: Centralized Saga-style orchestrator preventing cross-domain anomalies.
- **Orders**: FSM-based immutable order states.
- **Payments**: Standardized payment gateway API integration stubs.
- **Shipping**: Provider-agnostic calculation engines.
- **Notifications**: Event-driven Celery asynchronous mailer.
- **Reviews & Reputation**: Anti-fraud metrics aggregating trusted buyer behavior.
- **Promotion Engine**: Mathematical evaluation trees and concurrent usage enforcement.
- **Analytics & Vendor Dashboard**: Lock-free atomic increment pipelines mapping directly to DRF endpoints.
