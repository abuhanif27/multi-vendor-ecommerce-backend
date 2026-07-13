# Backend Architecture

This document describes the architectural principles of the Multi-Vendor E-commerce Backend.

Its purpose is to keep the codebase consistent, maintainable, scalable, and easy to understand as the project grows.

---

# Architecture Philosophy

The project follows a layered architecture.

Each layer has a single responsibility.

Business logic is separated from HTTP concerns.

The architecture prioritizes:

- Readability
- Maintainability
- Testability
- Reusability
- Scalability

---

# Request Lifecycle

Every request follows the same flow.

```
Client
    │
    ▼
URL Router
    │
    ▼
APIView
    │
    ▼
Serializer
    │
    ▼
Service
    │
    ▼
Model
    │
    ▼
Database
```

Response

```
Database
    │
    ▼
Model
    │
    ▼
Serializer
    │
    ▼
APIView
    │
    ▼
Client
```

Each layer has a clearly defined responsibility.

No layer should perform the responsibility of another layer.

---

# Layer Responsibilities

## URL

Responsible for routing requests.

Responsibilities

- Map URLs to views
- API versioning

Should never contain

- Business logic
- Validation

---

## API View

Views are responsible for HTTP.

Responsibilities

- Receive requests
- Authentication
- Permissions
- Selecting serializer
- Returning HTTP responses
- Passing context

Views should remain thin.

Views should never contain business logic.

Example

```python
serializer.save(...)
```

Good

```python
ProductService.create(...)
```

Better

---

## Serializer

Serializers are responsible for transforming and validating data.

Responsibilities

- Validate request data
- Serialize model instances
- Deserialize JSON
- Simple validation

Examples

- Email format
- Password confirmation
- Required fields
- Maximum image count

Serializers should not contain

- Transactions
- Complex business logic
- Database coordination
- Cross-service workflows

---

## Service

Services contain business logic.

Responsibilities

- Transactions
- Business rules
- Multi-model operations
- Complex updates
- Database coordination

Examples

```
ProductImageService

CheckoutService

PaymentService

InventoryService
```

Services should not know anything about

- HTTP
- Requests
- Responses
- DRF serializers

Services should work with plain Python objects.

Example

Good

```python
ProductImageService.insert(
    product=product,
    image=image,
)
```

Avoid

```python
ProductImageService.insert(
    validated_data,
)
```

---

## Model

Models represent the database.

Responsibilities

- Database schema
- Relationships
- Constraints
- Computed properties

Models should remain focused on persistence.

Avoid placing application workflows inside models.

---

# Dependency Direction

Dependencies always point downward.

```
View
    ↓
Serializer
    ↓
Service
    ↓
Model
```

Never reverse the dependency.

Good

```
View
    ↓
Service
```

Bad

```
Service
    ↓
APIView
```

Good

```
Serializer
    ↓
Service
```

Bad

```
Model
    ↓
Serializer
```

---

# Business Logic

Business logic belongs inside services.

Examples

Good

- Checkout
- Product image ordering
- Inventory updates
- Payment processing

Bad

- APIViews
- Models
- Serializers

---

# Transactions

Operations affecting multiple database records must use transactions.

Example

```python
with transaction.atomic():
    ...
```

Examples

- Checkout
- Product image ordering
- Stock updates

Never leave the database in a partially updated state.

---

# Database Optimization

Always optimize queries.

Use

```
select_related()
```

for

- ForeignKey
- OneToOne

Use

```
prefetch_related()
```

for

- ManyToMany
- Reverse ForeignKey

Avoid N+1 query problems.

---

# Service Pattern

Every service should expose a simple public API.

Example

```
ProductImageService

├── insert()
├── delete()
└── move()
```

Private helper methods begin with an underscore.

Example

```
_resolve_sort_order()

_shift_up()

_shift_down()
```

Views should only call public methods.

Never call private methods outside the service.

---

# Validation Strategy

Validation belongs in serializers.

Business workflows belong in services.

Example

Serializer

- Maximum 5 images
- Required fields
- Data types

Service

- Shift image ordering
- Create image
- Delete image
- Move image

---

# Permissions

Authorization belongs in permission classes.

Examples

```
IsVendor

IsShopOwner

IsProductOwner
```

Avoid permission logic inside views.

---

# Query Strategy

Views should define optimized querysets.

Example

```python
.select_related(
    "shop",
    "category",
)
.prefetch_related(
    "images",
)
```

Avoid unnecessary queries.

---

# Mixins

Mixins encapsulate reusable lookup logic.

Examples

```
ProductLookupMixin

ProductImageLookupMixin
```

Responsibilities

- Cached lookups
- Ownership checks
- Optimized object retrieval

Mixins should never contain business logic.

---

# Custom Generic Views

Shared DRF behavior should live in `apps.common`.

Example

```
UpdateDestroyAPIView
```

Avoid duplicating GenericAPIView combinations.

---

# Error Handling

Use DRF exceptions whenever possible.

Examples

```
ValidationError

PermissionDenied

NotFound
```

Avoid returning manual error responses when a DRF exception already exists.

---

# Reusability

If business logic is used in multiple places, extract it.

Examples

```
Serializer

↓

Service

↓

Management Command

↓

Celery

↓

Admin
```

All should be able to reuse the same service.

---

# Project Growth Strategy

As the project grows, every feature follows the same structure.

```
views/

serializers/

services/

permissions/

filters/

schema/
```

Each feature remains independent.

---

# Design Principles

## Single Responsibility Principle

Each class should have one reason to change.

Examples

APIView

↓

HTTP

Serializer

↓

Validation

Service

↓

Business Logic

Model

↓

Persistence

---

## Explicit Over Implicit

Write code that is easy to understand.

Prefer

```python
ProductImageService.delete(...)
```

Over

```python
image.delete()
```

when business rules are involved.

---

## Thin Views

Views coordinate requests.

They should not perform work.

---

## Fat Services

Complex business logic belongs inside services.

---

## Keep Models Simple

Models define data.

Services define behavior.

---

## Optimize Early for Readability

Readable code is easier to maintain than clever code.

Favor clarity over brevity.

---

# Testing Strategy

Tests should primarily target services.

Because services contain business logic.

Views should only verify

- Status codes
- Authentication
- Permissions
- Serialization

---

# Future Architecture

Future modules should follow the same architecture.

Examples

```
Orders

Payments

Inventory

Coupons

Reviews

Wishlist

Cart

Notifications
```

Each module should contain

- Views
- Serializers
- Services
- Permissions
- Filters
- Schema

Consistency is more valuable than cleverness.

---

# Core Principles

- Layered architecture
- REST-first design
- Thin views
- Focused serializers
- Fat services
- Simple models
- Explicit dependencies
- Reusable business logic
- Optimized database queries
- Transaction-safe operations
- Predictable project structure
- Consistency over cleverness