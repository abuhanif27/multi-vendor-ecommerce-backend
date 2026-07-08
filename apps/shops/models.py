from django.db import models
from django.utils.text import slugify
from django.conf import settings
from apps.common.models import UUIDModel, TimeStampedModel


class ProductStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"
    ARCHIVED = "archived", "Archived"


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
        max_length=255,
    )

    status = models.CharField(
        max_length=20,
        choices=ShopStatus.choices,
        default=ShopStatus.PENDING,
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            suffix = 2

            while Shop.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{suffix}"
                suffix += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["-created_at"]


class Product(UUIDModel, TimeStampedModel):
    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name="products",
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
            base_slug = slugify(self.name)
            slug = base_slug
            suffix = 2

            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{suffix}"
                suffix += 1

            self.slug = slug

        super().save(*args, **kwargs)

    class Meta:
        ordering = ["-created_at"]
