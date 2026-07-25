# SSLCommerz Payment Gateway Operational Runbook

## Overview
This runbook covers the operational and troubleshooting guidelines for the SSLCommerz Sandbox integration.

## 1. Environment Variables
To enable SSLCommerz integration, the following environment variables must be populated in the production environment (e.g. `.env` file). **Never hardcode these values.**

```env
SSLCOMMERZ_STORE_ID=your_store_id
SSLCOMMERZ_STORE_PASSWORD=your_store_password
SSLCOMMERZ_SANDBOX=True # Set to False for production
```

## 2. Callback URLs
The gateway relies on the following endpoints to confirm payment status from SSLCommerz. Ensure your frontend or API Gateway correctly routes these back to the `multi-vendor-ecommerce-backend`.

- **Success / IPN:** `POST /api/v1/payments/sslcommerz/success/` & `POST /api/v1/payments/sslcommerz/ipn/`
- **Fail:** `POST /api/v1/payments/sslcommerz/fail/`
- **Cancel:** `POST /api/v1/payments/sslcommerz/cancel/`

*Note: Both Success and IPN triggers backend validation via `SSLCommerzGateway.validate_payment`.*

## 3. Sandbox Setup
1. Visit the [SSLCommerz Sandbox Developer Portal](https://developer.sslcommerz.com/).
2. Generate your Sandbox `STORE_ID` and `STORE_PASSWORD`.
3. Set `SSLCOMMERZ_SANDBOX=True` in your `.env`.
4. Run standard checkout flows to trigger the redirect.

## 4. Payment State Machine 
The Payment aggregate enforces strict state transitions.
- `PENDING` → `CAPTURED`: Successful validation API response matching exact amount.
- `PENDING` → `FAILED`: Invalid credentials, validation API failure, amount mismatch, or user abandonment.
- `PENDING` → `CANCELLED`: User clicked Cancel on gateway.
- `CAPTURED` → `REFUNDED`: Administrator successfully initiates a refund workflow.

*Any transition from `CAPTURED` to `FAILED` is strictly blocked by the idempotency lock.*

## 5. Common Failure Scenarios & Troubleshooting

### Scenario A: Payment "Success" on Gateway, but Order Remains PENDING
- **Symptom:** User was charged/redirected, but order status didn't change.
- **Cause:** Webhook unreachable, or Validation API failed (e.g., amount mismatch).
- **Action:** 
  1. Check backend logs for `SSLCommerz Validation Failed`. 
  2. Verify that `payment.amount` exactly matched the `amount` in the validation response payload.
  3. Verify network connectivity to `https://sandbox.sslcommerz.com/validator/api/validationserverAPI.php`.

### Scenario B: Duplicate Callbacks (IPN + Success Webhook)
- **Symptom:** Both endpoints fire for the same transaction simultaneously.
- **Cause:** Normal behavior from SSLCommerz.
- **Action:** None required. The system leverages row-level locking (`select_for_update()`) on the `Payment` table. The first callback transitions the state to `CAPTURED`, and the second returns HTTP 200 idempotently.

### Scenario C: Initialization Failed
- **Symptom:** User clicks checkout, receives a 500 or PaymentInitializationFailed.
- **Cause:** Invalid `STORE_ID` or `STORE_PASSWORD`.
- **Action:** Check the `.env` values and restart the application server.

## 6. Observability
- All gateway integrations log under the `apps.payments.api.webhooks` and `apps.payments.gateways.sslcommerz` loggers.
- Latency issues and `requests.exceptions.RequestException` will trigger `PaymentGatewayUnavailable` exceptions and log as `ERROR`.
- Sensitive `card_no` is captured as raw metadata but is inherently masked by SSLCommerz payload structure (e.g., `444444XXXXXX1111`).
