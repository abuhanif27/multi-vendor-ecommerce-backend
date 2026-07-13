from rest_framework import generics, mixins


class UpdateDestroyAPIView(
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    generics.GenericAPIView,
):
    """
    Concrete view for updating and deleting a model instance.
    """

    def patch(self, request, *args, **kwargs):
        return self.partial_update(
            request,
            *args,
            **kwargs,
        )

    def delete(self, request, *args, **kwargs):
        return self.destroy(
            request,
            *args,
            **kwargs,
        )
