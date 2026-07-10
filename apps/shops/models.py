from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django_filters.rest_framework import DjangoFilterBackend
from apps.shops.filters import ProductFilter
from apps.common.models import UUIDModel, TimeStampedModel
from apps.common.mixins import SlugMixin
from apps.catalog.models import Category


class Shop(UUIDModel, TimeStampedModel, SlugMixin):
    class ShopStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        SUSPENDED = "suspended", "Suspended"
        REJECTED = "rejected", "Rejected"

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
        max_length=255,
    )

    status = models.CharField(
        max_length=20,
        choices=ShopStatus.choices,
        default=ShopStatus.PENDING,
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.generate_unique_slug(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["-created_at"]


class Product(UUIDModel, TimeStampedModel, SlugMixin):
    class ProductStatus(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name="products",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products',
    )
    name = models.CharField(
        max_length=255,
    )

    slug = models.SlugField(
        unique=True,
        max_length=255,
    )

    description = models.TextField(blank=True)

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )

    stock = models.PositiveIntegerField(
        default=0,
    )

    status = models.CharField(
        max_length=20,
        choices=ProductStatus.choices,
        default=ProductStatus.DRAFT,
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.generate_unique_slug(self.name)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["-created_at"]
