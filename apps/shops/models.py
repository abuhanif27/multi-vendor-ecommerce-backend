from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from apps.common.models import UUIDModel, TimeStampedModel
from apps.common.mixins import SlugMixin
from apps.catalog.models import Category, CategoryAttributeValue


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
        db_index=True,
    )
    
    # Reputation metrics
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    review_count = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._create_unique_slug(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["-created_at"]


class Product(UUIDModel, TimeStampedModel, SlugMixin):
    class ProductStatus(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        REJECTED = "rejected", "Rejected"
        SUSPENDED = "suspended", "Suspended"
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

    status = models.CharField(
        max_length=20,
        choices=ProductStatus.choices,
        default=ProductStatus.DRAFT,
        db_index=True,
    )

    # Reputation metrics
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    review_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._create_unique_slug(self.name)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["-created_at"]


class ProductVariant(UUIDModel, TimeStampedModel):
    """
    Represents a purchasable variant of a product.

    Examples:

        MacBook Pro
            - 16GB / 512GB / Silver
            - 32GB / 1TB / Space Black

        Nike Air Max
            - Black / Size 41
            - White / Size 42
    """

    class VariantStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants",
    )

    sku = models.CharField(
        max_length=100,
        unique=True,
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0.01),
        ],
    )

    barcode = models.CharField(
        max_length=100,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=VariantStatus.choices,
        default=VariantStatus.ACTIVE,
    )

    class Meta:
        ordering = (
            "-created_at",
        )

    def __str__(self):
        return f"{self.product.name} ({self.sku})"


class VariantAttributeValue(UUIDModel, TimeStampedModel):
    """
    Stores the selected value of an attribute for a product variant.

    Example:

        Variant:
            MAC-16-512-SLV

        Selections:
            RAM -> 16 GB
            Storage -> 512 GB
            Color -> Silver
    """

    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name="attribute_values",
    )

    category_attribute_value = models.ForeignKey(
        CategoryAttributeValue,
        on_delete=models.PROTECT,
        related_name="variant_values",
    )

    class Meta:
        ordering = (
            "created_at",
        )

        constraints = [
            models.UniqueConstraint(
                fields=(
                    "variant",
                    "category_attribute_value",
                ),
                name="unique_value_per_variant",
            ),
        ]

    def __str__(self):
        return (
            f"{self.variant.sku} → "
            f"{self.category_attribute_value}"
        )


class ProductImage(UUIDModel, TimeStampedModel):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
    )

    image = models.ImageField(
        upload_to="products/",
    )

    alt_text = models.CharField(
        max_length=255,
        blank=True,
    )

    display_order = models.PositiveSmallIntegerField(
        default=1,
    )

    is_primary = models.BooleanField(
        default=False,
    )

    class Meta:
        ordering = ("display_order", "created_at")
        constraints = [
            models.UniqueConstraint(
                fields=("product",),
                condition=models.Q(is_primary=True),
                name="unique_primary_product_image",
            ),
        ]

    def __str__(self):
        return f"{self.product.name} - Image {self.display_order}"


class VariantImage(UUIDModel, TimeStampedModel):
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name="images",
    )

    image = models.ImageField(
        upload_to="variants/",
    )

    alt_text = models.CharField(
        max_length=255,
        blank=True,
    )

    display_order = models.PositiveSmallIntegerField(
        default=1,
    )

    is_primary = models.BooleanField(
        default=False,
    )

    class Meta:
        ordering = ("display_order", "created_at")
        constraints = [
            models.UniqueConstraint(
                fields=("variant",),
                condition=models.Q(is_primary=True),
                name="unique_primary_variant_image",
            ),
        ]

    def __str__(self):
        return f"{self.variant.sku} - Image {self.display_order}"
