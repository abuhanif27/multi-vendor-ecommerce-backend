# Coding Style Guide

This document defines the coding standards for the project.

The goal is to keep the codebase consistent, readable, maintainable, and easy to review.

These conventions apply to every Django app in the project.

---

# Philosophy

Code is written for humans first.

Readable code is more valuable than clever code.

Favor explicitness over shortcuts.

Consistency is more important than personal preference.

---

# General Principles

- Keep code simple.
- Keep functions small.
- Prefer readability over brevity.
- Prefer explicit code over magic.
- Avoid unnecessary abstractions.
- Write code another developer can understand quickly.

---

# Naming

Use descriptive names.

Good

```python
product_image
current_image_count
requested_sort_order
```

Bad

```python
img
cnt
tmp
x
```

---

# Variables

Variables should describe their purpose.

Good

```python
current_image_count
```

Bad

```python
count
```

---

Good

```python
requested_sort_order
```

Bad

```python
value
```

---

# Boolean Variables

Boolean names should read naturally.

Good

```python
is_vendor

is_verified

has_permission

can_update
```

Avoid

```python
vendor

verified

permission
```

---

# Function Names

Functions should describe an action.

Good

```python
create_product()

send_verification_email()

move_image()
```

Avoid

```python
product()

email()

image()
```

---

# Class Names

Use PascalCase.

Examples

```python
ProductImageService

RegisterSerializer

ShopDetailAPIView

ProductFilter
```

---

# Constants

Constants use UPPER_CASE.

```python
MAX_PRODUCT_IMAGES = 5

DEFAULT_PAGE_SIZE = 20
```

Avoid magic numbers.

Bad

```python
if images.count() >= 5:
```

Better

```python
if images.count() >= MAX_PRODUCT_IMAGES:
```

---

# Imports

Import order

1. Python Standard Library

```python
import uuid
```

2. Third-Party Packages

```python
from rest_framework import serializers
```

3. Django

```python
from django.db import transaction
```

4. Local Applications

```python
from apps.shops.models import Product
```

Separate groups with one blank line.

---

# Class Order

Inside a class, use this order.

```python
class ProductSerializer:

    class Meta

    serializer fields

    validation methods

    create()

    update()

    helper methods
```

---

APIView

```python
class ProductAPIView:

    attributes

    get_queryset()

    get_serializer_class()

    get_permissions()

    perform_create()

    helper methods
```

---

# Functions

Keep functions focused.

A function should perform one task.

Good

```python
def _shift_up():
```

Avoid

```python
def process_everything():
```

---

# Function Length

Prefer functions under 30 lines.

If longer, consider splitting into helper methods.

---

# Method Visibility

Public methods

```python
insert()

delete()

move()
```

Private methods

```python
_shift_up()

_shift_down()

_resolve_sort_order()
```

Views should only call public methods.

---

# Comments

Comment **why**, not **what**.

Good

```python
# Close the gap after deleting an image.
```

Bad

```python
# Add 1 to sort_order.
```

The code already shows *what* it does.

---

# Docstrings

Use docstrings for

- public classes
- services
- complex methods

Example

```python
class ProductImageService:
    """
    Business logic for product image management.
    """
```

---

# Line Length

Prefer readable lines.

Break long expressions vertically.

Good

```python
Product.objects.select_related(
    "shop",
    "category",
)
```

Avoid

```python
Product.objects.select_related("shop", "category")
```

---

# Chained QuerySets

Each queryset method should appear on its own line.

Good

```python
return (
    Product.objects
    .select_related(
        "shop",
        "category",
    )
    .prefetch_related(
        "images",
    )
    .filter(
        status=Product.Status.ACTIVE,
    )
)
```

Avoid

```python
Product.objects.select_related("shop").filter(...)
```

---

# Conditionals

Avoid nested if statements.

Prefer early returns.

Good

```python
if user is None:
    return

...
```

Avoid

```python
if user:
    ...
```

with deep nesting.

---

# Services

Services should expose simple public APIs.

Good

```python
ProductImageService.insert()

ProductImageService.move()

ProductImageService.delete()
```

Avoid exposing private helper methods.

---

# Serializers

Serializers should validate data.

Avoid business workflows.

Good

```python
validate()

create()

update()
```

Avoid

- transactions
- complex queries
- multi-model operations

---

# Views

Views should coordinate.

Responsibilities

- Authentication
- Permissions
- Serializer
- Response

Avoid

- business logic
- transactions
- SQL updates

---

# Models

Models define data.

Good

- fields
- relationships
- computed properties

Avoid

- business workflows
- HTTP logic

---

# Transactions

Always wrap multi-step database operations.

Good

```python
with transaction.atomic():
```

---

# F Expressions

Prefer database-side updates.

Good

```python
.update(
    sort_order=F("sort_order") + 1,
)
```

Avoid

```python
for image in images:
    image.sort_order += 1
    image.save()
```

---

# Exceptions

Raise DRF exceptions when appropriate.

Good

```python
ValidationError

PermissionDenied

NotFound
```

Avoid manually constructing error responses in views.

---

# Duplication

Avoid duplicated logic.

Extract repeated business logic into services.

Extract repeated lookup logic into mixins.

---

# Type Hints

Type hints are encouraged for utility functions and services.

Example

```python
def create_order(
    *,
    user: User,
) -> Order:
```

---

# Logging

Use logging for unexpected situations.

Do not use print().

---

# TODO Comments

Avoid permanent TODOs.

Bad

```python
# TODO: Fix later
```

Instead create an issue or implement immediately.

---

# Magic Numbers

Avoid

```python
5

100

86400
```

Prefer named constants.

---

# API Views

Prefer GenericAPIView and DRF generic views.

Avoid APIView unless generic views cannot solve the problem.

---

# Business Logic Checklist

Before writing business logic ask:

Does this belong in

View?

Serializer?

Service?

Model?

Put it in the lowest appropriate layer.

---

# Code Review Checklist

Before committing

- Is the code readable?
- Is the naming clear?
- Is business logic in services?
- Is validation in serializers?
- Is the view thin?
- Is the queryset optimized?
- Is duplication avoided?
- Is transaction.atomic() needed?
- Can another developer understand this quickly?

---

# Core Principles

- Readability first
- Explicit over implicit
- Thin views
- Focused serializers
- Fat services
- Simple models
- Small functions
- Descriptive naming
- Consistency over cleverness
- Write code for the next developer