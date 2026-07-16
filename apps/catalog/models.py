from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError

from apps.common.models import UUIDModel, TimeStampedModel


class Category(UUIDModel, TimeStampedModel):
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
        null=True,
        blank=True,
        related_name="children",
    )

    is_active = models.BooleanField(
        default=True,
    )

    def clean(self):
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
        self.full_clean()

        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
