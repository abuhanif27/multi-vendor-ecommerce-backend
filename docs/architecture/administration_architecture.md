# Administration Architecture (Refined)

## 1. Domain Model
The Administration domain orchestrates the platform and maintains the immutable ledger of staff actions. It does not duplicate business rules from core domains.

### 1.1 Core Entities
*   **AdminAuditLog:** Generic, immutable platform infrastructure recording state-changing actions across all domains. Includes success/failure results.
*   **FeatureFlag:** Simple boolean toggles controlling the availability of platform features.
*   **PlatformSetting:** Strongly typed global configuration settings (e.g., base commission rate).

### 1.2 Architecture Decision Record (ADR): Configuration Value Storage
**Context:** Storing strongly typed values in a relational database for global configuration.
**Decision:** We chose "Option B" (a single `JSONField` paired with a `value_type` string) instead of storing everything as plain text strings.
**Justification:** While text strings require explicit parsing (e.g., `if type == 'boolean': return value == 'True'`), a `JSONField` natively deserializes Python primitives (booleans, integers, floats, dictionaries) at the ORM boundary. The service layer guarantees the JSON conforms to the declared `value_type` using strict `.clean()` validation. This provides runtime safety and elegant type coercion without complex parsing logic.

## 2. RBAC Architecture Evaluation
Rather than reinventing a custom Role-Based Access Control system, we will leverage **Django's native `Group` and `Permission` system**.
*   **Django Permissions:** These perfectly map to granular strings (e.g., `administration.can_approve_vendor`, `administration.can_force_refund`). We will define custom permissions within the Administration domain's `Meta` class.
*   **Django Groups:** These serve as our "Roles" (e.g., "Vendor Manager", "Support Agent"). A Super Admin simply assigns users to Groups via the native Django Admin or a future API.
*   **Object-Level Permissions:** While tools like `django-guardian` exist, they add significant overhead. We do not currently need Row-Level Security for internal staff (e.g., "Agent A can only moderate Category X"). Global permissions are sufficient.
*   **Conclusion:** The native Django system natively fulfills our requirement for flexible RBAC without the technical debt of a custom abstraction. We will strictly use `user.has_perm('app_label.permission_codename')`.

## 3. Capability-Focused Services
Instead of a single "God Service", Administration is divided into highly cohesive, single-responsibility services. These services *orchestrate* domain logic; they do not own it.

*   **VendorAdministrationService:**
    *   `approve_shop(shop_id, admin_user, reason)`: Delegates to `ShopService.approve()`, creates Audit log.
    *   `suspend_vendor(vendor_id, admin_user, reason)`: Delegates to `ShopService.suspend()` and `ProductService.unlist_all()`, creates Audit log.
*   **ProductModerationService:**
    *   `unlist_product(product_id, admin_user, reason)`: Delegates to `ProductService.update_status()`, creates Audit log.
*   **RefundAdministrationService:**
    *   `force_refund(order_id, admin_user, reason)`: Delegates to `PaymentService.refund()`, creates Audit log.
*   **DisputeAdministrationService:**
    *   `arbitrate_dispute(...)`
*   **PlatformConfigurationService:**
    *   `set_feature_flag(key, is_active, admin_user)`
    *   `update_global_setting(key, value, admin_user)`
*   **AuditService:**
    *   `log_action(actor, action_type, resource_type, resource_id, before_state, after_state, reason, ip_address, user_agent)`

## 4. Administration Events
The Administration domain publishes strictly typed events to the global `EventBus`:

*   `VendorApprovedEvent(shop_id, admin_id)`
*   `VendorSuspendedEvent(vendor_id, admin_id, reason)`
*   `ProductModeratedEvent(product_id, action, admin_id, reason)`
*   `RefundForcedEvent(order_id, amount, admin_id, reason)`
*   `FeatureFlagChangedEvent(key, is_active, admin_id)`
*   `PlatformSettingUpdatedEvent(key, new_value, admin_id)`

## 5. Implementation Plan (Sequential Flow)
1. **Staff Permissions:** Native Django Groups mapping to capability string permissions.
2. **Audit Logging:** Immutable `AdminAuditLog` enforcing immutability natively.
3. **Platform Configuration:** `FeatureFlag` and `PlatformSetting`. 
    - **Cache Flow:** Read-through cache with configurable TTL (default 3600s). `update_setting` performs synchronous cache invalidation.
    - **Audit Flow:** Settings actively wrap `AuditService.log_action()` creating immutable traces of `before_state` and `after_state`.
4. **Vendor Administration:** Orchestrates existing modules to manage shop statuses.
5. **Product Moderation:** Orchestrates Catalog to un-list items.
