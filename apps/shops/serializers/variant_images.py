from rest_framework import serializers

from apps.shops.models import VariantImage
from apps.shops.services import VariantImageService


class VariantImageReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = VariantImage
        fields = (
            "id",
            "image",
            "alt_text",
            "display_order",
            "is_primary",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class VariantImageWriteSerializer(serializers.ModelSerializer):
    is_primary = serializers.BooleanField(required=False, default=False)
    display_order = serializers.IntegerField(required=False, write_only=True)

    class Meta:
        model = VariantImage
        fields = (
            "image",
            "alt_text",
            "is_primary",
            "display_order",
        )

    def validate(self, attrs):
        if "variant" not in self.context:
            raise AssertionError(
                "VariantImageWriteSerializer requires "
                "'variant' in serializer context."
            )

        return attrs

    def create(self, validated_data):
        alt_text = validated_data.get("alt_text", "")
        image = validated_data["image"]

        return VariantImageService.create(
            variant=self.context["variant"],
            image=image,
            alt_text=alt_text,
        )

    def update(self, instance, validated_data):
        if "alt_text" in validated_data:
            instance = VariantImageService.update(
                variant_image=instance,
                alt_text=validated_data["alt_text"],
            )

        if validated_data.get("is_primary"):
            VariantImageService.set_primary(variant_image=instance)
            
        return instance
