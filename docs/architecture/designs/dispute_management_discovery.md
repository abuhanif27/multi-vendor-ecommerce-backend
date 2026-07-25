# Phase 3: Dispute Management - Discovery & Domain Analysis

## 1. Business Goals
- **Purpose:** Provide a structured channel for resolving disagreements between Buyers and Vendors regarding orders that could not be resolved through normal workflows (e.g., standard returns/refunds).
- **Problems Solved:** Ensures platform integrity by allowing administrative oversight when a Vendor is unresponsive or unfair, or when a Buyer is making unreasonable demands. It prevents off-platform escalation and standardizes the mediation process.
- **Participating Actors:** Customer (Buyer), Vendor (Seller), Administrator (Mediator).

## 2. Actors
- **Customer:** Can open a dispute if dissatisfied with an order or a vendor's decision (e.g., a rejected return). Communicates evidence.
- **Vendor:** Responds to the dispute, provides counter-evidence, and can offer resolutions (e.g., partial refund, full refund).
- **Administrator:** Mediates escalated disputes, makes a final binding decision, and executes the resolution via platform tools (forced refunds, account strikes).

## 3. Dispute Lifecycle (State Machine)
- **OPEN:** The customer has initiated the dispute. The vendor is notified and expected to respond.
- **VENDOR_REVIEW:** The vendor is actively reviewing and communicating with the customer to reach a resolution without admin intervention.
- **ESCALATED:** The vendor and customer could not agree, or the vendor was unresponsive. The dispute is escalated to Platform Administrators.
- **ADMIN_REVIEW:** An administrator is actively investigating the dispute, reviewing evidence, and communicating with both parties.
- **RESOLVED:** A final decision was reached (either by mutual agreement or administrative fiat) and the necessary actions (refunds/returns) have been executed. Terminal state.
- **REJECTED:** The administrator determined the dispute was invalid or fraudulent. Terminal state.
- **CANCELLED:** The customer voluntarily withdrew the dispute before a resolution was forced. Terminal state.

## 4. Resolution Outcomes
To keep the lifecycle independent from the business result, a `ResolutionOutcome` field is introduced. When a dispute moves to `RESOLVED` (or `REJECTED`), it is tagged with an outcome:
- **CUSTOMER_FAVOUR:** Decision made in favor of the customer.
- **VENDOR_FAVOUR:** Decision made in favor of the vendor.
- **MUTUAL_SETTLEMENT:** Both parties agreed to a resolution.
- **ADMIN_OVERRIDE:** An administrator forced a specific resolution outside normal bounds.
- **OTHER:** Special cases.

*Note: The actual orchestrations (Refund, Return Required, etc.) are executed as side effects alongside the outcome tagging.*

## 5. Integration Points
The Dispute aggregate acts as an orchestrator across domains:
- **Orders:** Disputes are tightly coupled to a `VendorOrder`.
- **Returns (Phase 2):** A dispute resolution might automatically generate an `APPROVED` Return request.
- **Refunds (Phase 1):** A dispute resolution might automatically call `PaymentService.process_refund()`.
- **Notifications / EventBus:** Publishes Integration Events (`DisputeOpenedEvent`, `DisputeEscalatedEvent`, `DisputeResolvedEvent`) to notify actors.
- **Audit:** All state changes, especially administrative fiat resolutions, must be logged to the `AdminAuditLog`.

## 6. Business Rules & Constraints
- **Eligibility:** 
  - Must the order be DELIVERED? Yes, disputes generally assume fulfillment has occurred or failed. (For Phase 3, we allow it on `DELIVERED` or `SHIPPED` if vastly delayed, but strict rule: `DELIVERED`).
  - Time Limit: Hard-coded assumption of 30 days post-delivery. (Configurable in future Global Settings).
- **Return Overlap:** A dispute *can* be opened while a Return is active (e.g., if the vendor rejected the return unfairly).
- **Refund Overlap:** A dispute *can* be opened after a partial refund, but generally not if a full refund was already issued.
- **Concurrency:** Only *one* active dispute may exist per `VendorOrder` at a time.
- **Finality:** Once a dispute reaches `RESOLVED`, `REJECTED`, or `CANCELLED`, it cannot be reopened. A new dispute cannot be opened for the same order if a terminal state was reached.

## 7. Non-Goals
The following are intentionally excluded from Phase 3:
- **Chargebacks:** Direct integration with credit card chargeback APIs.
- **External Arbitration:** Legal mediation APIs.
- **AI-assisted Fraud Detection:** Automated dispute resolution or risk scoring.
- **Multi-currency Settlement:** Handling currency fluctuations during refunds.
- **Accounting Exports:** Generating ledger reports for external ERPs.
- **Automated Vendor Penalties:** Suspending vendors automatically based on dispute ratios (this remains a manual Admin action for now).
