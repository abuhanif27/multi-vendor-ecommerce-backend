from rest_framework.response import Response
from rest_framework import (
    status,
)
from django.utils.text import slugify


class ReadSerializerMixin:
    read_serializer_class = None

    def get_read_serializer(self, instance):
        if self.read_serializer_class is None:
            raise NotImplementedError(
                "read_serializer_class must be defined."
            )

        return self.read_serializer_class(
            instance,
            context=self.get_serializer_context(),
        )


class SlugMixin:
    def _create_unique_slug(self, value):
        base_slug = slugify(value)
        slug = base_slug
        counter = 2

        while type(self).objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        return slug


class ReadResponseMixin:
    """
    Return the read serializer representation after
    successful create and update operations.

    Views using this mixin must implement:

        - get_read_serializer(instance)
    """

    def create(
        self,
        request,
        *args,
        **kwargs,
    ):
        serializer = self.get_serializer(
            data=request.data,
        )
        serializer.is_valid(
            raise_exception=True,
        )

        instance = serializer.save()

        read_serializer = self.get_read_serializer(
            instance,
        )

        headers = self.get_success_headers(
            read_serializer.data,
        )

        return Response(
            read_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    def update(
        self,
        request,
        *args,
        **kwargs,
    ):
        partial = kwargs.pop(
            "partial",
            False,
        )

        instance = self.get_object()

        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        instance = serializer.save()

        return Response(
            self.get_read_serializer(instance).data,
        )
