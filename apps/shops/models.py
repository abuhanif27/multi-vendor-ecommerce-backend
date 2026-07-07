from django.db import models

from django.conf import settings
from apps.common.models import UUIDModel, TimeStampedModel


class ShopStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    SUSPENDED = "suspended", "Suspended"
    REJECTED = "rejected", "Rejected"


class Shop(UUIDModel, TimeStampedModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shops",
    )

    name = models.CharField(
        max_length=255,
    )

    slug = models.SlugField(
        unique=True,
    )

    status = models.CharField(
        max_length=20,
        choices=ShopStatus.choices,
        default=ShopStatus.PENDING,
    )
