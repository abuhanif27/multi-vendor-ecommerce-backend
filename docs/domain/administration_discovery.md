# Marketplace Administration: Domain Discovery & Requirements (Final)

## 1. Domain Vision
The Marketplace Administration domain is the central nervous system of the multi-vendor commerce platform. It transforms the system from a technical engine into a manageable, governable business asset. 

Administration is not a monolith; it is cleanly divided into two distinct operational contexts:
*   **Marketplace Operations:** The business layer. Overseeing users, vendors, products, and financial disputes.
*   **Platform Operations:** The infrastructure layer. Overseeing the marketplace's own configuration, security, auditability, and staff governance.

## 2. Structural Breakdown

### 2.1. Marketplace Operations (Business Admin)
This context focuses on the day-to-day curation and arbitration of the multi-vendor ecosystem.
*   **Vendor & Shop Management:** Reviewing applications, verifying identities, and suspending bad actors.
*   **Product Moderation:** Reviewing flagged products and enforcing catalog safety policies.
*   **Review Moderation:** Hiding or deleting abusive feedback to maintain trust.
*   **Order Oversight & Refunds:** Intervening in stuck orders or executing forced manual refunds.
*   **Dispute Resolution:** Arbitrating conflicts where buyers and sellers cannot reach an agreement.

### 2.2. Platform Operations (System Admin)
This context focuses on the overarching governance of the platform itself.
*   **Staff Management & RBAC:** Provisioning operational staff and managing dynamic permission groups.
*   **Audit Logging:** Maintaining the immutable record of all privileged actions.
*   **Feature Flags:** Dynamically enabling or disabling platform capabilities without deployments.
*   **Platform Configuration:** Managing global settings like commission rates or taxonomy trees.
*   **Background Task Monitoring:** Ensuring Celery workers (emails, webhooks) are functioning.
*   **System Health & Announcements:** Viewing DB/Redis health and broadcasting site-wide banners to users.

## 3. Dynamic RBAC (Role-Based Access Control)
Hardcoded boolean flags (e.g., `is_moderator`) do not scale. Administration requires a flexible RBAC model:
*   **Permissions:** Granular, string-based capabilities (e.g., `admin:refunds:force`, `admin:vendors:approve`).
*   **Roles / Permission Groups:** Collections of permissions forming a business persona (e.g., "Tier 2 Support").
*   **Dynamic Assignment:** A staff member can hold multiple Roles. Roles can be edited dynamically by a Super Administrator without altering business logic. The application code strictly checks Permissions, never Roles.

## 4. Immutable Audit Logging
Accountability requires strict audit trails. Every state-changing privileged action MUST write to an immutable `AdminAuditLog` capturing:
*   **Actor:** The staff user who initiated the action.
*   **Action:** The specific operation performed (e.g., `VENDOR_SUSPENDED`).
*   **Resource Type:** The affected entity (e.g., `Shop`).
*   **Resource ID:** The PK of the affected entity.
*   **Timestamp:** The exact time of the action.
*   **Before State:** JSON representation of the entity before the change.
*   **After State:** JSON representation of the entity after the change.
*   **IP Address & User Agent:** Captured from the request for security tracking.
*   **Reason/Comment:** Optional (but often required by UX) text explaining *why* the action was taken.

## 5. Approval Workflows
Governance requires manual intervention at specific gateways:
*   **Vendor Approval:** A new user requests vendor status -> Enters `PENDING_VERIFICATION` queue -> Vendor Manager reviews ID/Tax docs -> Status changes to `APPROVED` or `REJECTED`.
*   **Shop Verification:** A vendor creates a shop -> Enters `PENDING` queue -> Reviewed for naming/branding violations -> Status changes to `APPROVED` or `REJECTED`.
*   **Product Approval:** If pre-moderation is enabled, products enter `PENDING_REVIEW` before going live. Alternatively, post-moderation allows products to be immediately active but flagged by users later for takedown.
*   **Refund Approval:** Large refunds may require dual-approval (a Support Agent requests it, a Finance Manager approves it).
*   **Account Suspension/Restoration:** A Vendor Manager suspends a vendor. All active products are immediately un-listed. Restoration re-lists the products.

## 6. Dashboard Requirements
The Admin interface will require a central dashboard aggregating the following widgets for immediate triage:
*   **Pending Vendor Approvals:** Count of shops waiting for review.
*   **Pending Product Moderation:** Count of user-flagged items.
*   **Open Disputes:** Count of unassigned escalation tickets.
*   **Refund Queue:** Count of pending manual refunds.
*   **Recent Audit Events:** A live ticker of the last 10 privileged actions.
*   **Platform Health Summary:** Red/Green status indicators for DB, Cache, Celery, and SMTP.
*   **Revenue Snapshot:** GMV and Platform Commission metrics over the last 24/48 hours.

## 7. Future Multi-Tenancy Architecture
While out of scope for V1, the Administration domain must be designed not to paint the architecture into a corner regarding multi-tenancy.
*   **Regional Marketplaces:** If the platform expands to `Daraz EU` and `Daraz NA`, the RBAC system must eventually support `Region` scoping (e.g., an Admin can only approve EU vendors).
*   **Multiple Brands:** If the backend powers multiple distinct storefronts, platform configurations (like commission rates) must be tied to a `TenantID` rather than being singular global rows.
*   **Consideration:** We will not implement multi-tenancy now, but we will ensure configuration tables and RBAC structures do not fundamentally break if a `tenant_id` column is added later.

## 8. Out of Scope (Bounded Context Preservation)
The Administration domain is an *orchestrator*. It does not own core business logic; it commands other domains.
*   **Not Auth:** Administration uses the existing `apps.authentication`. It does not invent new token mechanisms.
*   **Not Orders/Payments/Shipping:** When an Admin forces a refund, Administration calls `PaymentService.refund()`. It does not execute raw payment API calls.
*   **Not Analytics:** Administration dashboards consume `AnalyticsService`. They do not duplicate the data warehouse.
