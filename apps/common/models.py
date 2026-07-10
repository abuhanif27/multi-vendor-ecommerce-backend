import uuid
from django.db import models
from django.utils.text import slugify


class UUIDModel(models.Model):
    """
    Abstract base model that provides a UUID primary key.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    """
    Abstract base model that provides timestamp fields.
    """

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="The date and time when this record was created.",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="The date and time when this record was last updated.",
    )

    class Meta:
        abstract = True


class SlugModel(models.Model):
    class Meta:
        abstract = True

    def generate_unique_slug(self, value):
        base_slug = slugify(value)
        slug = base_slug
        counter = 2

        while type(self).objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        return slug
