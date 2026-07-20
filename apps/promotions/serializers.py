from rest_framework import serializers
from apps.promotions.models import Promotion, Coupon, PromotionCondition, PromotionReward

class PromotionConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromotionCondition
        fields = ['id', 'condition_type', 'min_amount', 'category', 'product', 'config']

class PromotionRewardSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromotionReward
        fields = ['id', 'reward_type', 'fixed_amount', 'percentage', 'max_discount_amount', 'config']

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ['id', 'code', 'max_uses', 'current_uses', 'max_uses_per_user', 'created_at']
        read_only_fields = ['id', 'current_uses', 'created_at']

class PromotionSerializer(serializers.ModelSerializer):
    conditions = PromotionConditionSerializer(many=True, read_only=True)
    reward = PromotionRewardSerializer(read_only=True)
    
    class Meta:
        model = Promotion
        fields = [
            'id', 'name', 'description', 'status', 'shop', 
            'priority', 'is_exclusive', 'start_date', 'end_date',
            'conditions', 'reward', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

# DTO Serializers for Public Validation API
class CartItemValidationSerializer(serializers.Serializer):
    product_id = serializers.UUIDField(required=False)
    category_id = serializers.UUIDField(required=False)
    shop_id = serializers.UUIDField(required=False)
    price = serializers.DecimalField(max_digits=12, decimal_places=2)
    quantity = serializers.IntegerField(min_value=1)

class ValidationRequestSerializer(serializers.Serializer):
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2)
    items = CartItemValidationSerializer(many=True)
    coupon_codes = serializers.ListField(child=serializers.CharField(), required=False, default=list)

class PricingBreakdownSerializer(serializers.Serializer):
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2)
    discount_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    shipping_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    tax_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    grand_total = serializers.DecimalField(max_digits=12, decimal_places=2)

class PromotionLineSerializer(serializers.Serializer):
    promotion_id = serializers.UUIDField()
    promotion_name = serializers.CharField()
    discount_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    is_free_shipping = serializers.BooleanField()

class CouponRejectionSerializer(serializers.Serializer):
    code = serializers.CharField()
    reason_code = serializers.CharField()
    reason_message = serializers.CharField()

class ValidationResponseSerializer(serializers.Serializer):
    pricing = PricingBreakdownSerializer()
    is_free_shipping = serializers.BooleanField()
    applied_promotions = PromotionLineSerializer(many=True)
    rejections = CouponRejectionSerializer(many=True)
