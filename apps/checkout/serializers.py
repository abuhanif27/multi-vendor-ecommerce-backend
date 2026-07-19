from rest_framework import serializers

class CheckoutItemSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    sku = serializers.CharField()
    product_name = serializers.CharField()
    shop_name = serializers.CharField()
    quantity = serializers.IntegerField()
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    item_total = serializers.DecimalField(max_digits=10, decimal_places=2)

class CheckoutWarningsSerializer(serializers.Serializer):
    inventory = serializers.ListField(child=serializers.CharField())
    price = serializers.ListField(child=serializers.CharField())
    unavailable_items = serializers.ListField(child=serializers.CharField())

class CheckoutSummarySerializer(serializers.Serializer):
    items = CheckoutItemSerializer(many=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)
    discounts = serializers.DecimalField(max_digits=10, decimal_places=2)
    shipping = serializers.DecimalField(max_digits=10, decimal_places=2)
    taxes = serializers.DecimalField(max_digits=10, decimal_places=2)
    total = serializers.DecimalField(max_digits=10, decimal_places=2)
    warnings = CheckoutWarningsSerializer()

class AddressSerializer(serializers.Serializer):
    street = serializers.CharField(max_length=255)
    city = serializers.CharField(max_length=100)
    state = serializers.CharField(max_length=100)
    postal_code = serializers.CharField(max_length=20)
    country = serializers.CharField(max_length=100)

class CheckoutProcessSerializer(serializers.Serializer):
    shipping_address = AddressSerializer()
    billing_address = AddressSerializer(required=False)
