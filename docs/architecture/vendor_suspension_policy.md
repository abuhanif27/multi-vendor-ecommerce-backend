# Vendor Suspension Policy

This document defines the business rules governing suspended vendors.

## 1. Authentication and Access
- **Can suspended vendors log in?** Yes. Their user accounts remain active, allowing them to communicate with support, access historical data, and manage their store's existing configurations/remediation tasks.

## 2. Product Management
- **Can suspended vendors create new products?** No. Product creation endpoints should block requests if the parent shop is suspended.
- **Can suspended vendors edit existing products?** Yes. Vendors must be able to remediate issues (e.g., fixing policy-violating descriptions or images) that may have caused the suspension.

## 3. Order and Fulfillment Lifecycle
- **Can suspended vendors receive new orders?** No. The shop and its products are hidden from the public storefront and checkout processes.
- **Can suspended vendors fulfill existing orders?** Yes. Existing commitments to customers must be honored. Fulfillment operations remain active for pre-suspension orders.

## 4. Public Storefront
- **Can customers browse products from suspended shops?** No. Suspended shops and their products are explicitly excluded from catalog searches, category listings, and direct URL access.

## 5. Administrative Requirements
- **Suspension Reason:** A reason is strictly required when suspending a vendor. This reason is securely captured in the `AdminAuditLog` and passed down through the `VendorSuspendedEvent` to inform downstream services (like email notifications).
- **Restoration:**
    - A shop can only be restored from the `SUSPENDED` state.
    - Restoration immediately returns the shop to the `APPROVED` state.
    - Restoration strictly creates a separate `UPDATE` audit log.
    - Restoration publishes the `VendorRestoredEvent` but does **not** re-trigger the initial "Welcome/Approved" onboarding flows.
