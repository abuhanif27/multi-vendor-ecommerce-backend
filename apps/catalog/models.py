from django.db import models
from django.utils.text import slugify

from apps.common.models import UUIDModel, TimeStampedModel


class Category(UUIDModel, TimeStampedModel):
    name = models.CharField(
        max_length=255,
        unique=True,
    )

    slug = models.SlugField(
        max_length=255,
        unique=True,
    )

    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="children",
    )

    is_active = models.BooleanField(
        default=True,
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 2

            while Category.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
