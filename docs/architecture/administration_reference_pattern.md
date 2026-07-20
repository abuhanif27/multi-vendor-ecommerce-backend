# Administration Reference Pattern

This document defines the canonical engineering pattern for all Marketplace Administration workflows. 
Any future administrative capability (e.g., Vendor Rejection, Suspension, Product Moderation, Refund Administration) **MUST** strictly adhere to this sequence.

## The Canonical Sequence

Every administrative operation modifying domain state must follow these exact steps in order:

1. **Permission Check:** Intercept the request at the orchestration layer (Service) and enforce granular RBAC (e.g., `has_perm('administration.can_approve_vendor')`).
2. **Idempotency Guard (Pre-Transaction):** Avoid creating empty audit records by returning early if the domain entity is already in the requested state.
3. **`transaction.atomic()`:** Open the transaction boundary.
4. **Domain Service Execution:** Delegate the actual business logic and database updates to the domain's native service (e.g., `ShopService.approve_shop()`). The domain service validates transitions and utilizes `select_for_update()` to prevent concurrency races.
5. **Audit Log:** Write an immutable `AdminAuditLog` capturing the exact `before_state`, `after_state`, the `actor`, and the `reason`.
6. **Observability Log:** Emit a structured Python log (e.g., `logger.info(..., extra={...})`) for Datadog/ELK tracing.
7. **`transaction.on_commit()`:** Safely queue the `EventBus` dispatch so downstream consumers (Notifications, Analytics) only react if the database transaction definitively succeeds.

## Code Example

```python
class VendorAdministrationService:
    @staticmethod
    def generic_admin_action(resource_id: str, actor: User, reason: str = None):
        # 1. Permission Check
        if not actor.has_perm('administration.can_do_action'):
            raise PermissionDenied("Insufficient permissions.")

        # 2. Idempotency Check (Domain-specific implementation might do this inside the transaction)
        
        with transaction.atomic():
            # 3. Domain Service Execution (with row locks)
            resource, changed = DomainService.do_action(resource_id)

            if not changed:
                return resource

            # 4. Audit Log
            AuditService.log_action(
                actor=actor,
                action="ACTION_NAME",
                resource_type="Resource",
                resource_id=resource_id,
                result="SUCCESS",
                before_state={"status": "OLD"},
                after_state={"status": "NEW"},
                reason=reason
            )
            
            # 5. Observability
            logger.info("Admin action successful", extra={"admin_id": actor.id})

            # 6. Event Dispatch on Commit
            event = DomainEvent(resource_id=resource_id, admin_id=actor.id)
            transaction.on_commit(lambda: EventBus.publish(event))

        return resource
```
