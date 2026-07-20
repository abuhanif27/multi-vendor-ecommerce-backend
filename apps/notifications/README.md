# Notifications API

This module exposes the frontend Inbox / Notification Bell endpoints. It strictly returns `IN_APP` channel notifications. Other channels like `EMAIL` and `SMS` are dispatched silently to the user without polluting the in-app bell.

## Base URL: `/api/v1/notifications/`
**All endpoints require the user to be authenticated.**

### 1. List Inbox
- **Method**: `GET`
- **URL**: `/api/v1/notifications/`
- **Description**: Returns a paginated list of notifications where `channel=IN_APP`.
- **Response**: Paginated standard DRF structure.

### 2. Mark Single Notification as Read
- **Method**: `PATCH`
- **URL**: `/api/v1/notifications/<uuid:pk>/read/`
- **Description**: Sets `read_at` to the current timestamp. Safe to call multiple times (idempotent).
- **Security**: Will return `404 Not Found` if the User attempts to read a notification belonging to another User.

### 3. Mark All Unread as Read
- **Method**: `POST`
- **URL**: `/api/v1/notifications/read-all/`
- **Description**: Bulk updates all `IN_APP` notifications where `read_at` is `null` to the current timestamp.
- **Response**: `{"detail": "Marked 4 notifications as read."}`
