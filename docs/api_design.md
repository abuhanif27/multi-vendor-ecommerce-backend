# API Design Guidelines

This document defines the API design conventions used throughout the project.

Following these conventions ensures consistency, maintainability, and a predictable developer experience.

---

# API Style

- API Style: REST
- Response Format: JSON
- Authentication: JWT
- Versioning: URL-based (`/api/v1/`)
- Resource Naming: Plural nouns
- Updates: PATCH
- Deletes: DELETE

---

# URL Structure

Base URL

```
/api/v1/
```

Example

```
/api/v1/products/
```

---

# Resource Naming

Use plural nouns.

✅ Good

```
/products/
/shops/
/categories/
/orders/
/users/
```

❌ Bad

```
/product/
/shop/
/category/
```

---

# Parent Resources

Parent resources use slugs.

Examples

```
/products/{product_slug}/

/shops/{shop_slug}/

/categories/{category_slug}/
```

Example

```
/products/dell-xps-13/

/shops/apple-store/

/categories/laptops/
```

---

# Nested Resources

Nested resources always use the parent slug.

Examples

```
/products/{product_slug}/images/

/products/{product_slug}/variants/

/products/{product_slug}/reviews/

/products/{product_slug}/questions/

/shops/{shop_slug}/products/

/shops/{shop_slug}/orders/
```

---

# Child Resources

Child resources use primary keys.

Examples

```
/products/{product_slug}/images/{pk}

/products/{product_slug}/variants/{pk}

/products/{product_slug}/reviews/{pk}
```

Reason

- Parent resources have business identity.
- Child resources are implementation details.
- Integer primary keys are sufficient.

---

# HTTP Methods

GET

Retrieve resources.

Examples

```
GET /products/

GET /products/dell-xps-13/
```

---

POST

Create a resource.

Examples

```
POST /products/

POST /products/dell-xps-13/images/
```

---

PATCH

Partially update a resource.

Examples

```
PATCH /products/dell-xps-13/images/5/

PATCH /shops/apple-store/
```

---

DELETE

Delete a resource.

Examples

```
DELETE /products/dell-xps-13/images/5/
```

---

PUT

Not used.

Reason

This project uses partial updates exclusively.

PATCH is sufficient for all update operations.

---

# Response Status Codes

200 OK

Successful retrieval or update.

Examples

```
GET

PATCH
```

---

201 Created

Resource successfully created.

Examples

```
POST
```

---

204 No Content

Resource successfully deleted.

Examples

```
DELETE
```

---

400 Bad Request

Validation failed.

Examples

- Invalid input
- Business rule violation

---

401 Unauthorized

Authentication required or invalid token.

---

403 Forbidden

Authenticated but lacks permission.

---

404 Not Found

Requested resource does not exist.

---

# Pagination

Collection endpoints use pagination.

Example

```
GET /products/
```

Response

```json
{
    "count": 120,
    "next": "...",
    "previous": null,
    "results": []
}
```

Detail endpoints are never paginated.

---

# Filtering

Filtering uses query parameters.

Example

```
GET /products/?category=laptops

GET /products/?min_price=500

GET /products/?max_price=2000
```

---

# Searching

Search uses the `search` query parameter.

Example

```
GET /products/?search=dell
```

---

# Ordering

Ordering uses the `ordering` query parameter.

Examples

```
GET /products/?ordering=price

GET /products/?ordering=-created_at

GET /products/?ordering=name
```

---

# Authentication

JWT Bearer Token.

Example

```
Authorization: Bearer <access_token>
```

---

# Ownership

Sensitive resources must verify ownership.

Examples

- Shop Owner
- Product Owner
- Order Owner

Ownership checks are implemented in custom permission classes.

---

# Serializer Responsibilities

Serializers are responsible for

- Input validation
- Output serialization

Serializers should not contain complex business logic.

---

# Service Responsibilities

Services are responsible for

- Business logic
- Transactions
- Complex operations
- Database coordination

Example

```
ProductImageService

CheckoutService

PaymentService
```

---

# View Responsibilities

Views are responsible for

- Authentication
- Permissions
- HTTP requests
- HTTP responses

Views should remain thin.

---

# Business Logic

Business logic belongs in the service layer.

Example

```
View
    ↓
Serializer
    ↓
Service
    ↓
Model
```

---

# Permissions

Permissions should be implemented using custom DRF permission classes.

Examples

```
IsVendor

IsShopOwner

IsProductOwner
```

Avoid permission logic inside views whenever possible.

---

# Swagger Documentation

Every public endpoint should include

- Summary
- Description
- Tags
- Request examples
- Response examples
- Status codes
- Error responses

---

# Project Conventions

Use slugs for public resources.

Use primary keys for nested child resources.

Prefer PATCH over PUT.

Use RESTful URLs.

Keep views thin.

Keep serializers focused on validation.

Move business logic into services.

Reuse business logic through service classes.

Avoid duplicated logic.

Optimize database access using

- select_related()
- prefetch_related()

Wrap multi-step database operations inside

```
transaction.atomic()
```

Use

```
F()
```

expressions for database-side updates whenever possible.

---

# Guiding Principles

- Consistency over cleverness.
- Explicit is better than implicit.
- Thin views.
- Fat services.
- Predictable APIs.
- REST-first design.
- Optimize for readability.
- Build for long-term maintainability.