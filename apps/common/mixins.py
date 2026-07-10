from django.utils.text import slugify


class SlugMixin:
    def _create_unique_slug(self, value):
        base_slug = slugify(value)
        slug = base_slug
        counter = 2

        while type(self).objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        return slug
