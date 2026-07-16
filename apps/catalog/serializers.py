from rest_framework import serializers

from apps.catalog.models import Category


class CategorySerializer(serializers.ModelSerializer):
    parent = serializers.SlugRelatedField(
        slug_field="slug",
        queryset=Category.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "parent",
            "is_active",
        )

        read_only_fields = (
            "id",
            "slug",
        )

    def validate_parent(self, parent):
        """
        Prevent circular category hierarchies.
        """

        if parent is None:
            return parent

        if self.instance is None:
            return parent

        ancestor = parent

        while ancestor is not None:
            if ancestor == self.instance:
                raise serializers.ValidationError(
                    "A category cannot be assigned to itself "
                    "or any of its descendants."
                )

            ancestor = ancestor.parent

        return parent
