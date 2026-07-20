# Administration Architecture

## 1. Domain Model

The Administration domain focuses on two primary areas: managing staff access (RBAC) and maintaining an immutable ledger of administrative actions (Audit). It acts as an orchestration layer interacting with all other platform domains.

### 1.1 Core Entities
*   **AdminRole:** Represents a collection of permissions.
*   **AdminPermission:** Represents a specific, granular capability (e.g., `admin:vendors:approve`).
*   **AdminUserRole:** Junction table linking a User to an AdminRole.
*   **AdminAuditLog:** Immutable ledger recording all state-changing actions performed by staff.
*   **FeatureFlag:** Global toggles for enabling/disabling platform features.
*   **PlatformSetting:** Key-value pairs for global configuration (e.g., base commission rate).
*   **SystemAnnouncement:** Sitewide banners or alerts for vendors/buyers.

## 2. Aggregate Boundaries

**Aggregate 1: Role-Based Access Control (RBAC)**
*   Root: `AdminRole`
*   Entities: `AdminPermission`, `AdminUserRole`
*   Rules: Superusers bypass role checks. Standard staff must possess the specific `AdminPermission` string required for an endpoint.

**Aggregate 2: Governance & Configuration**
*   Root: `PlatformSetting`
*   Entities: `FeatureFlag`, `SystemAnnouncement`
*   Rules: Singleton-like access for key-value settings.

**Aggregate 3: Audit**
*   Root: `AdminAuditLog`
*   Rules: Append-only. No updates or hard deletes allowed.

*(Note: Marketplace Operations like approving a vendor or moderating a product do not require new database models in the Admin domain. Instead, the Admin domain will provide Services that orchestrate state changes on the `Shop` or `Product` models living in their respective domains, wrapping those actions in an `AdminAuditLog`.)*

## 3. Services

*   **RBACService:** 
    *   `assign_role(user, role)`
    *   `has_permission(user, permission_string)`
    *   `get_user_permissions(user)`
*   **AuditService:**
    *   `log_action(actor, action, resource_type, resource_id, before_state, after_state, request_metadata)`
*   **MarketplaceOpsService:** (Orchestrator)
    *   `approve_shop(shop_id, admin_user, reason)`: Calls `ShopService.approve()`, then `AuditService.log_action()`.
    *   `suspend_vendor(vendor_id, admin_user, reason)`: Calls `ShopService.suspend()` and `ProductService.unlist_all()`, then logs it.
    *   `force_refund(order_id, admin_user, reason)`: Calls `PaymentService.refund()`, then logs it.
*   **PlatformOpsService:**
    *   `set_feature_flag(key, is_active)`
    *   `update_global_setting(key, value)`

## 4. Events

The Administration domain will heavily publish events, allowing other domains to react:
*   `ShopApprovedEvent`: Handled by Notifications (email vendor).
*   `VendorSuspendedEvent`: Handled by Catalog (hide products) and Cart (remove invalid items).
*   `RefundForcedEvent`: Handled by Payments/Accounting.
*   `GlobalSettingChangedEvent`: Cache invalidation triggers.

## 5. Permissions

Granular strings strictly separated by business capability. Examples:
*   `admin:platform:read`, `admin:platform:write`
*   `admin:rbac:read`, `admin:rbac:write`
*   `admin:vendors:read`, `admin:vendors:write`
*   `admin:products:read`, `admin:products:write`
*   `admin:orders:read`, `admin:orders:write`
*   `admin:finance:read`, `admin:finance:write`

## 6. APIs (Namespace: `/api/v1/admin/`)

### 6.1. Platform Operations (System Admin)
*   `GET /api/v1/admin/roles/`
*   `POST /api/v1/admin/roles/{id}/assign/`
*   `GET /api/v1/admin/audit-logs/` (Filter by actor, resource, date)
*   `GET /api/v1/admin/settings/`
*   `PATCH /api/v1/admin/settings/{key}/`

### 6.2. Marketplace Operations (Business Admin)
*   `GET /api/v1/admin/shops/pending/`
*   `POST /api/v1/admin/shops/{id}/approve/`
*   `POST /api/v1/admin/shops/{id}/reject/`
*   `POST /api/v1/admin/vendors/{id}/suspend/`
*   `GET /api/v1/admin/products/reported/`
*   `POST /api/v1/admin/products/{id}/unlist/`
*   `POST /api/v1/admin/orders/{id}/force-refund/`

## 7. Implementation Plan

1.  **Phase 1: Foundation (RBAC & Audit)**
    *   Implement `AdminRole`, `AdminPermission`, and RBAC middleware/permission classes.
    *   Implement `AdminAuditLog` and the `AuditService`.
2.  **Phase 2: Platform Configuration**
    *   Implement `PlatformSetting`, `FeatureFlag`.
    *   Build the Platform Operations REST APIs.
3.  **Phase 3: Marketplace Orchestration**
    *   Implement `MarketplaceOpsService` to wrap existing cross-domain actions (Vendor Approval, Unlisting, Refunds) in Audit logs.
    *   Build the Marketplace Operations REST APIs using strict RBAC permission checks.
4.  **Phase 4: Analytics & Dashboard**
    *   Implement dashboard readout endpoints aggregating data from `AnalyticsService` and `AdminAuditLog`.
