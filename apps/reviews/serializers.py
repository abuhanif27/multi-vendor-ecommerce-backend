from rest_framework import serializers
from apps.reviews.models import ProductReview, ProductReviewMedia, ShopReview, ShopReviewMedia, ProductReviewReport, ShopReviewReport
from django.contrib.auth import get_user_model

User = get_user_model()

class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name']
        read_only_fields = fields

class ProductReviewReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductReviewReport
        fields = ['id', 'reporter', 'review', 'reason', 'is_resolved', 'created_at']
        read_only_fields = ['id', 'reporter', 'review', 'is_resolved', 'created_at']

class ShopReviewReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopReviewReport
        fields = ['id', 'reporter', 'review', 'reason', 'is_resolved', 'created_at']
        read_only_fields = ['id', 'reporter', 'review', 'is_resolved', 'created_at']

class ProductReviewMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductReviewMedia
        fields = ['id', 'file_url', 'media_type', 'created_at']
        read_only_fields = ['id', 'created_at']

class ProductReviewSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)
    media = ProductReviewMediaSerializer(many=True, read_only=True)
    
    # Input fields for creation
    order_item_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = ProductReview
        fields = [
            'id', 'user', 'product', 'order_item_id', 'rating', 
            'comment', 'status', 'is_edited', 'media', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'status', 'is_edited', 'created_at', 'updated_at', 'product']

class ShopReviewMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopReviewMedia
        fields = ['id', 'file_url', 'media_type', 'created_at']
        read_only_fields = ['id', 'created_at']

class ShopReviewSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)
    media = ShopReviewMediaSerializer(many=True, read_only=True)
    
    # Input fields for creation
    vendor_order_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = ShopReview
        fields = [
            'id', 'user', 'shop', 'vendor_order_id', 'rating', 
            'comment', 'status', 'is_edited', 'media', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'status', 'is_edited', 'created_at', 'updated_at', 'shop']
