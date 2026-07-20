# Contributing Guidelines

Thank you for contributing to the Core Commerce Platform. To maintain the structural integrity of this senior-level codebase, all contributions must adhere to the following strict architectural rules.

## The Iron Rules

### 1. No Business Logic in Views
Views (`views.py`) are strictly for HTTP routing, permission checking, and payload parsing. 
**Forbidden:**
```python
# BAD
def create(self, request):
    order = Order.objects.create(...)
    if order.total > 100:
        order.apply_discount()
```
**Required:**
```python
# GOOD
def create(self, request):
    # Serializer parsing
    dto = OrderCreationDTO(**serializer.validated_data)
    # Delegation
    result = OrderService.create_order(dto)
    return Response(result)
```

### 2. Thin Serializers
DRF Serializers should only contain field definitions. `create()`, `update()`, and validation logic requiring database hits should be pushed to the Service layer.

### 3. Use DTOs for Contracts
Never pass raw dictionaries across domain boundaries. Define a `@dataclass` in `dtos.py` to strongly type the data contract.

### 4. Respect transaction.atomic()
If a Service mutates multiple rows (e.g., deducting inventory and writing an order), wrap the entire block in `transaction.atomic()`. Do NOT trap `IntegrityError` randomly. Let the database enforce constraints.

## Pull Request Process
1. Write Tests: Code without test coverage in `tests/` will be rejected.
2. Ensure you have not violated any Architectural Decision Records (see `docs/adr/`).
3. Format with Black and Ruff before submitting.
