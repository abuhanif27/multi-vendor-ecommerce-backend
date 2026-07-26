import re
import os

# Files to patch
files = [
    "apps/promotions/views.py",
    "apps/shops/views/products.py",
    "apps/shops/views/shops.py",
    "apps/notifications/views.py",
    "apps/orders/views.py",
    "apps/shipping/views.py",
    "apps/inventory/views.py",
]

for file in files:
    with open(file, 'r') as f:
        content = f.read()
    
    # We want to insert `if getattr(self, "swagger_fake_view", False): return self.serializer_class.Meta.model.objects.none()`
    # Actually, the simplest is `if getattr(self, "swagger_fake_view", False): return type(self)().get_queryset().model.objects.none()` - wait no.
    # Just return `None` or an empty list, DRF Spectacular might be happy, but let's just use empty queryset of the model.
    # Let's just manually patch them.
