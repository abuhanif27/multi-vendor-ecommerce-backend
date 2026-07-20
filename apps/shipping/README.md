# Shipping Module APIs

This module exposes endpoints for both Buyers to track their orders, and Vendors to manage the physical fulfillment of goods.

## Endpoints

### 1. Buyer: List Shipments
- **Method**: `GET`
- **URL**: `/api/v1/shipping/my-shipments/`
- **Query Params**: `?order_id=<uuid>` (Required)
- **Permission**: `IsAuthenticated` (Buyer must own the parent Order)
- **Description**: Returns all shipments associated with a specific checkout. Includes the Courier details and the append-only `tracking_events` timeline so the frontend can draw a vertical progress bar.

### 2. Vendor: View Shipment Detail
- **Method**: `GET`
- **URL**: `/api/v1/shipping/shipments/<uuid:pk>/`
- **Permission**: `IsVendor` (Vendor must own the Shop fulfilling the order)
- **Description**: Retrieves full shipment details including the `shipping_address_snapshot` that the vendor must print on the box.

### 3. Vendor: Assign Courier
- **Method**: `POST`
- **URL**: `/api/v1/shipping/shipments/<uuid:pk>/assign-courier/`
- **Permission**: `IsVendor`
- **Payload**:
  ```json
  {
      "courier_id": "<uuid>",
      "tracking_number": "PT-123456"
  }
  ```
- **Description**: Assigns the courier and automatically generates a clickable `tracking_url` based on the Courier's strategy template.

### 4. Vendor: Update FSM Status
- **Method**: `PATCH`
- **URL**: `/api/v1/shipping/shipments/<uuid:pk>/update-status/`
- **Permission**: `IsVendor`
- **Payload**:
  ```json
  {
      "status": "SHIPPED",
      "location": "Dhaka Hub",
      "description": "Package dropped off."
  }
  ```
- **Description**: Advances the finite state machine. Raises 400 Bad Request if the vendor attempts an illegal transition (e.g. skipping from PENDING directly to DELIVERED).
