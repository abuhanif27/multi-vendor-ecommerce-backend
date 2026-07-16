from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

from apps.common.models import TimeStampedModel, UUIDModel


class Category(UUIDModel, TimeStampedModel):
    """
    Product category.

    Supports hierarchical categories through the self-referencing
    `parent` relationship.
    """

    name = models.CharField(
        max_length=255,
        unique=True,
    )

    description = models.TextField(
        blank=True,
    )

    slug = models.SlugField(
        max_length=255,
        unique=True,
    )

    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        related_name="children",
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = (
            "name",
        )

    def clean(self):
        """
        Prevent circular category hierarchies.
        """

        super().clean()

        if self.parent is None:
            return

        ancestor = self.parent

        while ancestor is not None:
            if ancestor == self:
                raise ValidationError(
                    {
                        "parent": (
                            "A category cannot be assigned to itself "
                            "or any of its descendants."
                        )
                    }
                )

            ancestor = ancestor.parent

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        self.full_clean()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class CategoryAttribute(UUIDModel, TimeStampedModel):
    """
    Defines an attribute that products in a category can use.

    Examples:
        Laptop -> RAM
        Laptop -> Storage
        T-Shirt -> Color
        Phone -> Screen Size
    """

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="attributes",
    )

    name = models.CharField(
        max_length=100,
    )

    is_required = models.BooleanField(
        default=False,
    )

    sort_order = models.PositiveSmallIntegerField(
        default=1,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = (
            "sort_order",
            "created_at",
        )

        constraints = [
            models.UniqueConstraint(
                fields=("category", "name"),
                name="unique_attribute_per_category",
            ),
        ]

    def __str__(self):
        return f"{self.category} → {self.name}"
