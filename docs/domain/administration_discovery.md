# Marketplace Administration: Domain Discovery & Requirements

## 1. Domain Vision
The Marketplace Administration domain is the central nervous system of the multi-vendor commerce platform. While buyers and vendors operate within localized constraints (their carts, their shops), the Administration domain holds the global context. Its primary purpose is to empower internal staff to maintain platform integrity, resolve cross-domain conflicts, curate quality, and monitor the operational and financial health of the marketplace without requiring direct developer intervention. It transforms the system from a technical engine into a manageable business asset.

## 2. Functional Requirements

### 2.1. Core Administration Modules
The following modules provide concrete business value by facilitating marketplace governance:

*   **Vendor & Shop Verification (Gatekeeping):** Ensures only legitimate businesses operate on the platform. Includes workflows for approving/rejecting vendor applications and suspending bad actors.
*   **Product & Review Moderation (Quality Control):** Tools to un-list counterfeit/illegal products and remove abusive reviews, maintaining buyer trust.
*   **Dispute & Refund Resolution (Arbitration):** When vendors and buyers cannot agree on a return, admins step in to arbitrate the order, override shipment statuses, or force manual refunds.
*   **Platform Taxonomy & Category Management (Curation):** Global control over the unified category tree, attributes, and tags to prevent catalog fragmentation.
*   **User Management (Governance):** Ability to ban buyers, reset passwords, or force MFA.
*   **System Health & Task Monitoring (DevOps Visibility):** Visibility into Celery task queues (e.g., failed emails, stuck webhooks) and database health metrics for technical administrators.
*   **Audit Logs (Traceability):** Immutable historical records answering "Who changed this order/vendor status and when?"
*   **Feature Flags & Settings (Agility):** Toggles to turn off specific payment gateways during an outage or adjust global marketplace commission rates dynamically.

### 2.2. User Roles, Personas, and Permissions
The principle of least privilege dictates strict boundaries between operational staff:

| Persona | Role | Responsibilities | Permissions & Restrictions |
| :--- | :--- | :--- | :--- |
| **System Operator** | Super Administrator | Total system ownership, emergency overrides, and staff provisioning. | **Permitted:** Full read/write across all modules, assign roles to staff. **Restricted:** None. |
| **Marketplace Director** | Platform Administrator | Overseeing the entire business operation, global settings, and taxonomies. | **Permitted:** Modify global commissions, taxonomies, view all metrics. **Restricted:** Cannot view system health logs or provision Super Admins. |
| **Vendor Success Lead** | Vendor Manager | Onboarding, verifying, and managing seller relations and payout schedules. | **Permitted:** Approve/Reject/Suspend Shops, adjust vendor tiers. **Restricted:** Cannot alter catalog categories or view buyer-side disputes. |
| **Moderator** | Content Moderator | Maintaining a safe catalog by reviewing reported products and toxic reviews. | **Permitted:** Un-list products, delete/hide reviews. **Restricted:** Cannot view financial payouts or modify vendor shop statuses. |
| **Tier 2 Agent** | Dispute / Support Agent | Arbitrating complex buyer-seller disputes (e.g., undelivered items). | **Permitted:** Force refunds, override order statuses. **Restricted:** Cannot modify product catalog or alter global platform settings. |
| **Accountant** | Finance Manager | Overseeing money movement, vendor payouts, and platform revenue. | **Permitted:** Read order financials, authorize vendor payouts, export financial reports. **Restricted:** Cannot modify user data or product catalogs. |
| **Compliance Officer** | Read-only Auditor | Ensuring the platform adheres to legal and financial regulations. | **Permitted:** Read-only access to audit logs, financial exports, and user histories. **Restricted:** Cannot perform *any* write operations. |

### 2.3. Core Workflows
*   **The Vendor Onboarding Funnel:** Registration -> Pending Verification -> Document Review by Vendor Manager -> Approved/Rejected.
*   **The Arbitration Workflow:** Buyer disputes order -> Vendor disputes buyer claim -> Ticket escalated -> Support Agent reviews communications/shipping logs -> Agent forces refund -> Vendor payout balance adjusted.
*   **The Moderation Takedown:** Automated flag (or user report) -> Product enters review queue -> Moderator un-lists product -> Automated email sent to Vendor -> Strike applied to Vendor account.

### 2.4. Audit, Compliance, and Security
*   **Audit Trail:** Every state-changing action executed by an administrator (POST, PUT, PATCH, DELETE) MUST be logged in a write-append-only `AdminAuditLog` detailing the `actor_id`, `action`, `target_resource`, `previous_state`, and `new_state`.
*   **Security:** Administrative APIs must be hosted under a distinct namespace (e.g., `/api/v1/admin/`) and require strict `is_staff=True` authentication combined with granular, role-based access control (RBAC).
*   **Compliance (GDPR/CCPA):** Auditors require specific interfaces to extract PII (Right to Access) or anonymize data (Right to be Forgotten) safely without breaking referential integrity (e.g., historical orders).

## 3. Non-Functional Requirements
*   **Scalability:** Admin endpoints must utilize asynchronous processing for bulk operations (e.g., un-listing 1,000 products by a banned vendor).
*   **Data Freshness (Reporting):** The Admin Dashboard metrics (GMV, active vendors) should rely on pre-calculated rollups rather than running heavy `COUNT` or `SUM` aggregations on the fly.
*   **Idempotency & Concurrency:** When a Support Agent attempts to force a refund simultaneously while a Vendor voluntarily refunds it, the system must utilize DB locks to prevent double-refunding.
*   **Availability:** The Admin interface should degrade gracefully. If the Analytics database replica is down, Core Order/User management must remain functional.

## 4. User Stories
1. **As a Content Moderator**, I want to view a queue of reported products so that I can quickly suspend items that violate platform policies.
2. **As a Vendor Manager**, I want to approve or reject new shop registrations so that only verified businesses can sell on the platform.
3. **As a Support Agent**, I want to force a manual refund on a disputed order so that the buyer is compensated when a vendor refuses to cooperate.
4. **As a Platform Admin**, I want to adjust the global commission rate applied to new sales so that we can adapt our revenue model dynamically.
5. **As a Read-Only Auditor**, I want to export a log of all manual refunds issued by Support Agents this month to verify compliance against fraud.

## 5. Acceptance Criteria (Example: Vendor Approval)
*   **Given** a vendor has submitted a shop for verification.
*   **When** a Vendor Manager views the verification queue.
*   **Then** they see the shop details and attached verification documents.
*   **When** the Manager clicks "Approve".
*   **Then** the `Shop.status` changes to `APPROVED`, an automated email is sent to the vendor, and a record is written to the `AdminAuditLog`.

## 6. Risks
*   **Role Creep:** Admins accumulating permissions over time leading to compromised accounts having too much blast radius. *Mitigation: Implement strict RBAC via groups, not individual user flags.*
*   **Accidental Bulk Actions:** An admin accidentally suspending an entire category tree, disabling millions of products. *Mitigation: Require secondary confirmation workflows or soft-deletes for destructive actions.*
*   **Query Performance:** The Admin dashboard inherently requires heavy cross-domain SQL queries. Unoptimized dashboards can crash the primary database. *Mitigation: Route heavy reads to replicas or heavily rely on the `AnalyticsService` rollups.*

## 7. Future Expansion Opportunities
*   **Impersonation:** Allowing Support Agents to securely log in "as the user" to debug UI issues without requiring the user's password (strictly logged).
*   **Automated Moderation via AI:** Integrating AI to automatically pre-score products for policy violations before placing them in the moderator queue.
*   **Custom Role Builder:** Moving beyond hardcoded roles to allow Platform Admins to create bespoke roles (e.g., "Holiday Support Temp") by selecting discrete permissions from a UI.
