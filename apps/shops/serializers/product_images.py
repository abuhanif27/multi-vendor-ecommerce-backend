from rest_framework import serializers

from apps.shops.models import ProductImage
from apps.shops.services import ProductImageService


class ProductImageReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
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


class ProductImageWriteSerializer(serializers.ModelSerializer):
    is_primary = serializers.BooleanField(required=False, default=False)
    display_order = serializers.IntegerField(required=False, write_only=True)

    class Meta:
        model = ProductImage
        fields = (
            "image",
            "alt_text",
            "is_primary",
            "display_order",
        )

    def validate(self, attrs):
        if "product" not in self.context:
            raise AssertionError(
                "ProductImageWriteSerializer requires "
                "'product' in serializer context."
            )

        product = self.context["product"]
        if self.instance is None and product.images.count() >= 10:  # arbitrary max, or maybe remove
            # Actually, I'll remove arbitrary max validation unless specified.
            pass

        return attrs

    def create(self, validated_data):
        alt_text = validated_data.get("alt_text", "")
        
        # We pop these out because create service doesn't use them directly
        # It handles display_order and is_primary internally
        image = validated_data["image"]

        # Delegate creation to the service layer.
        return ProductImageService.create(
            product=self.context["product"],
            image=image,
            alt_text=alt_text,
        )

    def update(self, instance, validated_data):
        # Update alt_text if provided
        if "alt_text" in validated_data:
            instance = ProductImageService.update(
                product_image=instance,
                alt_text=validated_data["alt_text"],
            )

        # set_primary if provided and True
        if validated_data.get("is_primary"):
            ProductImageService.set_primary(product_image=instance)
            
        return instance
