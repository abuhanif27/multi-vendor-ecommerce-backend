from django.db import models


class UserRole(models.TextChoices):
    CUSTOMER = "customer", "Customer"
    VENDOR = "vendor", "Vendor"
    STAFF = "staff", "Staff"
