from rest_framework import serializers
from apps.cart.models import Cart, CartItem
from apps.shops.models import ProductVariant

class CartItemVariantReadSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    shop_name = serializers.CharField(source='product.shop.name', read_only=True)
    
    class Meta:
        model = ProductVariant
        fields = ('id', 'sku', 'price', 'product_name', 'shop_name')


class CartItemReadSerializer(serializers.ModelSerializer):
    variant = CartItemVariantReadSerializer(read_only=True)
    item_total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ('id', 'variant', 'quantity', 'unit_price', 'item_total', 'created_at')

    def get_item_total(self, obj):
        # We calculate total based on current live price rather than snapshot
        # Actually, if we use live price, we should multiply by variant price.
        # But for Cart, user sees snapshot until it is validated, or we show live price.
        # Let's show live price.
        return obj.variant.price * obj.quantity


class CartReadSerializer(serializers.ModelSerializer):
    items = CartItemReadSerializer(many=True, read_only=True)
    cart_total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ('id', 'status', 'items', 'cart_total', 'created_at')

    def get_cart_total(self, obj):
        return sum(item.variant.price * item.quantity for item in obj.items.all())


class CartItemWriteSerializer(serializers.Serializer):
    sku = serializers.CharField(max_length=100)
    quantity = serializers.IntegerField(min_value=1)

class CartItemUpdateSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)
