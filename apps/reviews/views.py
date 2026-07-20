from rest_framework import viewsets, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django.core.exceptions import ValidationError
from django.db.models import Prefetch

from apps.reviews.models import ProductReview, ShopReview, ReviewStatus, ProductReviewReport, ShopReviewReport
from apps.reviews.serializers import ProductReviewSerializer, ShopReviewSerializer, ProductReviewReportSerializer, ShopReviewReportSerializer
from apps.reviews.permissions import IsReviewOwnerOrReadOnly
from apps.reviews.services.review import ReviewService
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema

class ProductReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ProductReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsReviewOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['rating']
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at'] # Default ordering

    def get_queryset(self):
        qs = ProductReview.objects.filter(status=ReviewStatus.PUBLISHED).select_related(
            'user'
        ).prefetch_related(
            'media'
        )
        
        # Optionally filter by product_id passed in URL kwargs (e.g. nested router or query param)
        product_id = self.request.query_params.get('product_id')
        if product_id:
            qs = qs.filter(product_id=product_id)
            
        # Media-only filter
        has_media = self.request.query_params.get('has_media')
        if has_media and has_media.lower() == 'true':
            qs = qs.filter(media__isnull=False).distinct()
            
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({"detail": "product_id is required."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            review = ReviewService.create_product_review(
                user=request.user,
                product_id=product_id,
                order_item_id=serializer.validated_data.get('order_item_id'),
                rating=serializer.validated_data.get('rating'),
                comment=serializer.validated_data.get('comment', "")
            )
            # Re-serialize created object
            response_serializer = self.get_serializer(review)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({"detail": list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        review = self.get_object()
        
        serializer = self.get_serializer(review, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        try:
            updated_review = ReviewService.update_product_review(
                user=request.user,
                review_id=review.id,
                rating=serializer.validated_data.get('rating'),
                comment=serializer.validated_data.get('comment')
            )
            response_serializer = self.get_serializer(updated_review)
            return Response(response_serializer.data)
        except ValidationError as e:
            return Response({"detail": list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        review = self.get_object()
        try:
            ReviewService.delete_product_review(user=request.user, review_id=review.id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValidationError as e:
            return Response({"detail": list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(request=ProductReviewReportSerializer, responses={201: ProductReviewReportSerializer})
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def report(self, request, pk=None):
        review = self.get_object()
        serializer = ProductReviewReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report = serializer.save(reporter=request.user, review=review)
        return Response(ProductReviewReportSerializer(report).data, status=status.HTTP_201_CREATED)

class ShopReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ShopReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsReviewOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['rating']
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']

    def get_queryset(self):
        qs = ShopReview.objects.filter(status=ReviewStatus.PUBLISHED).select_related(
            'user'
        ).prefetch_related(
            'media'
        )
        
        shop_id = self.request.query_params.get('shop_id')
        if shop_id:
            qs = qs.filter(shop_id=shop_id)
            
        # Media-only filter
        has_media = self.request.query_params.get('has_media')
        if has_media and has_media.lower() == 'true':
            qs = qs.filter(media__isnull=False).distinct()
            
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        shop_id = request.data.get('shop_id')
        if not shop_id:
            return Response({"detail": "shop_id is required."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            review = ReviewService.create_shop_review(
                user=request.user,
                shop_id=shop_id,
                vendor_order_id=serializer.validated_data.get('vendor_order_id'),
                rating=serializer.validated_data.get('rating'),
                comment=serializer.validated_data.get('comment', "")
            )
            response_serializer = self.get_serializer(review)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({"detail": list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        review = self.get_object()
        
        serializer = self.get_serializer(review, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        try:
            updated_review = ReviewService.update_shop_review(
                user=request.user,
                review_id=review.id,
                rating=serializer.validated_data.get('rating'),
                comment=serializer.validated_data.get('comment')
            )
            response_serializer = self.get_serializer(updated_review)
            return Response(response_serializer.data)
        except ValidationError as e:
            return Response({"detail": list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        review = self.get_object()
        try:
            ReviewService.delete_shop_review(user=request.user, review_id=review.id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValidationError as e:
            return Response({"detail": list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(request=ShopReviewReportSerializer, responses={201: ShopReviewReportSerializer})
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def report(self, request, pk=None):
        review = self.get_object()
        serializer = ShopReviewReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report = serializer.save(reporter=request.user, review=review)
        return Response(ShopReviewReportSerializer(report).data, status=status.HTTP_201_CREATED)
