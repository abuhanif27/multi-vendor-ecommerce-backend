# Capability 4: Vendor Administration Workflow Design

## 1. Objective
Design the complete Vendor Approval lifecycle—from initial shop submission to operational status—acting as an orchestration layer over existing domains (Shops, Notifications, Analytics) without duplicating business logic.

## 2. Workflow Orchestration
1. **Submission:** A Vendor registers and submits a Shop profile via the `ShopService`. The shop is natively created with `status=PENDING`.
2. **Review:** A Vendor Manager (Staff) reviews the application using the Administration dashboard.
3. **Execution:** The Vendor Manager clicks "Approve" (or "Reject"), firing an API call to `VendorAdministrationService`.
4. **Validation:** The service checks RBAC permissions (`can_approve_vendor`). It ensures the Shop is currently in the `PENDING` state.
5. **State Mutation:** The service delegates to `ShopService.update_status(shop_id, 'APPROVED')`.
6. **Auditing:** The service calls `AuditService.log_action()` to create an immutable ledger entry.
7. **Event Publication:** The service publishes `VendorApprovedEvent` to the EventBus.
8. **Reactivity:** 
   - *Notifications Domain:* Listens to the event and sends a "Welcome to the Marketplace" email.
   - *Analytics Domain:* Listens to the event to increment the active vendor count.

## 3. State Machine & Transitions
The workflow relies on strict state transitions to prevent invalid business states.

**Allowed Transitions:**
*   `PENDING` → `APPROVED` (Vendor Manager accepts application)
*   `PENDING` → `REJECTED` (Vendor Manager declines application)
*   `APPROVED` → `SUSPENDED` (Vendor Manager suspends bad actor)
*   `SUSPENDED` → `APPROVED` (Vendor Manager restores an account)

**Invalid Transitions (Will raise ValidationError):**
*   `APPROVED` → `APPROVED` (Duplicate approval)
*   `REJECTED` → `APPROVED` (Rejected applications are terminal; vendor must reapply)
*   `PENDING` → `SUSPENDED` (Cannot suspend an unverified shop)

## 4. Domain Responsibilities
*   **Administration (`VendorAdministrationService`):** Orchestrator. Checks permissions, calls other services, writes to audit log, triggers events.
*   **Shop Domain (`ShopService`):** Data Owner. Mutates the `status` field. Enforces core validation (e.g. valid shop name).
*   **Notification Domain:** Consumer. Listens to events and handles SMTP transmission.
*   **Analytics Domain:** Consumer. Updates materialized views / metrics rollups.

## 5. Service Design
```python
class VendorAdministrationService:
    @staticmethod
    def approve_vendor(shop_id: int, actor: User, reason: str = None) -> Shop:
        pass
        
    @staticmethod
    def reject_vendor(shop_id: int, actor: User, reason: str) -> Shop:
        pass
        
    @staticmethod
    def suspend_vendor(shop_id: int, actor: User, reason: str) -> Shop:
        pass
        
    @staticmethod
    def restore_vendor(shop_id: int, actor: User, reason: str = None) -> Shop:
        pass
```

## 6. Events
Strictly typed events published to the `EventBus` post-transaction:
*   `VendorApprovedEvent(shop_id: int, admin_id: int)`
*   `VendorRejectedEvent(shop_id: int, admin_id: int, reason: str)`
*   `VendorSuspendedEvent(shop_id: int, admin_id: int, reason: str)`
*   `VendorRestoredEvent(shop_id: int, admin_id: int)`

## 7. Permissions
Granular capability flags bound to Django's native permission system (`administration.can_...`):
*   `can_approve_vendor`
*   `can_reject_vendor`
*   `can_suspend_vendor`
*   `can_restore_vendor`

## 8. API Design (REST)
**Base Namespace:** `/api/v1/admin/vendors/`
*(All endpoints require `IsAdminUser` and specific `has_perm()` checks)*

| Action | HTTP | Endpoint | Request Body | Response | Codes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Approve** | POST | `/{id}/approve/` | `{"reason": "Valid docs"}` | `200 OK` (Shop details) | 200, 400, 403, 404 |
| **Reject** | POST | `/{id}/reject/` | `{"reason": "Invalid ID"}` | `200 OK` (Shop details) | 200, 400, 403, 404 |
| **Suspend** | POST | `/{id}/suspend/` | `{"reason": "Fraud"}` | `200 OK` (Shop details) | 200, 400, 403, 404 |
| **Restore** | POST | `/{id}/restore/` | `{"reason": "Resolved"}` | `200 OK` (Shop details) | 200, 400, 403, 404 |

## 9. Test Plan
Comprehensive unit/integration tests before deployment:
1.  **Success Path:** Admin approves PENDING shop → Shop becomes APPROVED → Audit Log is created.
2.  **Event Firing:** Verify `VendorApprovedEvent` is dispatched securely.
3.  **Permission Denied:** Staff missing `can_approve_vendor` receives `403 Forbidden`.
4.  **Invalid State Transition:** Attempting to approve an already `APPROVED` shop raises `ValidationError`.
5.  **Rejection Validation:** Attempting to reject a shop without providing a `reason` payload raises `ValidationError`.
