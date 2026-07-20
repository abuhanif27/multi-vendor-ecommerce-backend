# ADR-001: The Service Layer Pattern

## Context
Django REST Framework (DRF) ecosystems commonly suffer from "Fat Views" or "Fat Serializers." Developers often embed complex logic (e.g., verifying inventory, writing to 3 different tables, dispatching emails) directly inside a DRF View's `post()` method or a Serializer's `create()` method. 
This ties business logic to the HTTP request cycle, making the code impossible to reuse via management commands or Celery tasks, and difficult to unit test without mocking HTTP request objects.

## Problem
How do we decouple our core e-commerce business rules from the Django REST Framework presentation layer?

## Decision
We enforce a strict **Service Layer Pattern**.
1. All domains must expose a `services.py` containing stateless python classes/functions.
2. Views and Serializers are forbidden from containing business logic. They may only parse inputs, call a Service, and serialize outputs.
3. Services communicate with each other using explicitly defined `@dataclass` DTOs (Data Transfer Objects), never raw dictionaries or raw QuerySets.

## Alternatives Considered
- **Fat Models**: Pushing logic down into Django Models. Rejected because e-commerce operations (like Checkout) span 4-5 different models. Picking one model to "own" the checkout is semantically incorrect and leads to God Classes.
- **Form Objects**: Rejected as they are closely tied to Django templates and UI concerns.

## Consequences
- **Pros**: 100% of business logic is callable from anywhere (Celery, management commands, views). Unit testing is significantly easier.
- **Cons**: Requires writing extra boilerplate (DTOs, explicit mapping in views) which slows down initial development speed compared to standard Django prototyping.

## Trade-offs
We traded rapid prototyping speed for long-term maintainability and modularity.
