# Project Structure

This document defines the directory structure of the project.

The goal is to keep the project organized, scalable, and easy to navigate as new features are added.

---

# Philosophy

The project follows a feature-based architecture.

Each Django app owns its own:

- Models
- Views
- Serializers
- Services
- Permissions
- Filters
- Schemas
- Tests

Feature-related code stays together.

Avoid organizing code by technical type across the entire project.

---

# Top-Level Structure

```
multi-vendor-ecommerce-backend/

├── apps/
├── config/
├── docs/
├── media/
├── static/
├── templates/
├── tests/
├── requirements/
├── manage.py
└── README.md
```

---

# apps/

Contains all Django applications.

Example

```
apps/

├── accounts/
├── common/
├── shops/
├── orders/
├── carts/
├── wishlist/
├── payments/
├── inventory/
├── reviews/
└── notifications/
```

Each app should be independent.

---

# config/

Contains project configuration.

```
config/

├── settings/
│   ├── base.py
│   ├── development.py
│   └── production.py
│
├── urls.py
├── asgi.py
├── wsgi.py
└── __init__.py
```

No business logic belongs here.

---

# docs/

Contains project documentation.

```
docs/

├── api_design.md
├── architecture.md
├── project_structure.md
├── coding_style.md
└── deployment.md
```

---

# requirements/

Dependency management.

Example

```
requirements/

├── base.txt
├── development.txt
└── production.txt
```

---

# Common App

Shared functionality belongs inside `apps/common`.

```
common/

├── permissions.py
├── pagination.py
├── views.py
├── exceptions.py
├── throttles.py
├── renderers.py
├── utils.py
└── constants.py
```

Only place code here if it is shared by multiple apps.

Never move app-specific logic into `common`.

---

# Feature App Structure

Every feature app follows the same layout.

Example

```
shops/

├── admin.py
├── apps.py
├── filters.py
├── mixins.py
├── models.py
├── permissions.py
├── signals.py
├── urls.py
├── tests.py
│
├── migrations/
│
├── schema/
│   ├── __init__.py
│   ├── shops.py
│   ├── products.py
│   └── product_images.py
│
├── serializers/
│   ├── __init__.py
│   ├── shops.py
│   ├── products.py
│   └── product_images.py
│
├── services/
│   ├── __init__.py
│   ├── product_images.py
│   ├── checkout.py
│   └── inventory.py
│
├── views/
│   ├── __init__.py
│   ├── shops.py
│   ├── products.py
│   └── product_images.py
│
└── management/
    └── commands/
```

---

# Views

Views handle HTTP.

Split large view files.

Good

```
views/

shops.py

products.py

product_images.py
```

Avoid

```
views.py

(1500+ lines)
```

---

# Serializers

Group serializers by feature.

Good

```
serializers/

products.py

shops.py

product_images.py
```

Avoid

```
serializers.py

(2000 lines)
```

---

# Services

Every business operation belongs here.

Examples

```
services/

product_images.py

checkout.py

inventory.py

payment.py
```

Service files should group related operations.

Example

```
ProductImageService

insert()

delete()

move()
```

---

# Schema

Swagger/OpenAPI documentation.

Split schema decorators by feature.

```
schema/

products.py

shops.py

product_images.py
```

Avoid putting all decorators inside views.

---

# Management Commands

```
management/

commands/

seed.py

clear_cache.py
```

Commands should reuse services.

Avoid duplicating business logic.

---

# Tests

Prefer feature-based tests.

Example

```
tests/

test_products.py

test_product_images.py

test_permissions.py
```

As the project grows, tests may become:

```
tests/

products/

orders/

payments/
```

---

# Import Order

Imports follow this order.

1. Python Standard Library

```
import os
```

2. Third-Party Packages

```
from rest_framework import generics
```

3. Django

```
from django.db import transaction
```

4. Local Apps

```
from apps.shops.models import Product
```

Separate each group with one blank line.

---

# File Size Guidelines

Recommended maximum sizes.

Views

≈300 lines

Serializers

≈300 lines

Services

≈400 lines

Models

≈300 lines

If a file grows significantly larger, split it.

These are guidelines, not strict limits.

---

# When to Create a New File

Create a new file when:

- A file becomes difficult to navigate.
- A feature is logically independent.
- Multiple developers may work on it.
- It improves discoverability.

Do not split files unnecessarily.

---

# Naming Conventions

Directories

```
services/

views/

serializers/

schema/
```

Use lowercase.

---

Files

```
products.py

shops.py

orders.py
```

Use snake_case.

---

Classes

```
ProductService

ProductSerializer

ProductAPIView
```

Use PascalCase.

---

Functions

```
create_product()

send_email()
```

Use snake_case.

---

Variables

```
product

shop

user
```

Use descriptive names.

Avoid abbreviations.

---

# Reusable Code

Ask this question before creating a helper.

> Will another feature use this?

If yes

Move it to

```
apps/common/
```

Otherwise

Keep it inside the feature app.

---

# Avoid

Avoid creating files like

```
helpers.py

misc.py

temp.py

utils.py
```

inside feature apps unless they have a very clear and narrow purpose.

Organize by feature, not by convenience.

---

# Future Growth

Every future app should follow the same structure.

Example

```
orders/

views/

serializers/

services/

schema/

permissions/

filters/
```

Consistency is mandatory.

---

# Core Principles

- Feature-first organization
- Keep related code together
- Split large files
- Thin views
- Focused serializers
- Fat services
- Shared code belongs in common
- Consistency over cleverness
- Optimize for maintainability