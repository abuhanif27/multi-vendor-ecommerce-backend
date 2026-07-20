from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.throttling import UserRateThrottle
from drf_spectacular.utils import extend_schema

from apps.promotions.models import Promotion, Coupon, PromotionCondition, PromotionReward
from apps.promotions.serializers import (
    PromotionSerializer, CouponSerializer, PromotionConditionSerializer, 
    PromotionRewardSerializer, ValidationRequestSerializer, ValidationResponseSerializer
)
from apps.promotions.permissions import IsVendorOwnerOrAdmin
from apps.promotions.services.promotion import PromotionService
from apps.promotions.dtos import CheckoutContextDTO

class PromotionViewSet(viewsets.ModelViewSet):
    """
    Admin and Vendor APIs to manage promotions.
    """
    serializer_class = PromotionSerializer
    permission_classes = [IsVendorOwnerOrAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Promotion.objects.all().order_by('-created_at')
        shop = user.shops.first()
        if shop:
            return Promotion.objects.filter(shop=shop).order_by('-created_at')
        return Promotion.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        shop = None
        # Vendors must link promotions to their shop
        if not (user.is_staff or user.is_superuser):
            shop = user.shops.first()
        serializer.save(shop=shop)

class PublicPromotionViewSet(viewsets.GenericViewSet):
    """
    Public APIs for buyers to view automatic promotions and validate coupons.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(request=ValidationRequestSerializer, responses=ValidationResponseSerializer)
    @action(detail=False, methods=['post'], url_path='validate', throttle_classes=[UserRateThrottle])
    def validate_cart(self, request):
        serializer = ValidationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        context = CheckoutContextDTO(
            user_id=request.user.id,
            subtotal=data['subtotal'],
            items=data['items'],
            coupon_codes=data.get('coupon_codes', [])
        )
        
        result = PromotionService.evaluate_cart(context)
        
        # Serialize DTO to Dict
        response_data = {
            "pricing": {
                "subtotal": result.pricing.subtotal,
                "discount_total": result.pricing.discount_total,
                "shipping_total": result.pricing.shipping_total,
                "tax_total": result.pricing.tax_total,
                "grand_total": result.pricing.grand_total,
            },
            "is_free_shipping": result.is_free_shipping,
            "applied_promotions": [
                {
                    "promotion_id": p.promotion_id,
                    "promotion_name": p.promotion_name,
                    "discount_amount": p.discount_amount,
                    "is_free_shipping": p.is_free_shipping
                } for p in result.applied_promotions
            ],
            "rejections": [
                {
                    "code": r.code,
                    "reason_code": r.reason_code,
                    "reason_message": r.reason_message
                } for r in result.rejections
            ]
        }
        
        response_serializer = ValidationResponseSerializer(data=response_data)
        response_serializer.is_valid(raise_exception=True)
        
        return Response(response_serializer.data, status=status.HTTP_200_OK)
