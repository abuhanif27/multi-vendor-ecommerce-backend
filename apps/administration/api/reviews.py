from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.exceptions import PermissionDenied
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from apps.reviews.models import ProductReview, ShopReview
from apps.administration.services.review_moderation import ReviewModerationService


class ModerateReviewRequestSerializer(serializers.Serializer):
    reason = serializers.CharField(required=True, allow_blank=False)

class RestoreReviewRequestSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True)


class BaseReviewModerationView(APIView):
    permission_classes = [IsAdminUser]

    def _execute_moderation(self, request, review_id, action_method, require_reason=True):
        serializer_class = ModerateReviewRequestSerializer if require_reason else RestoreReviewRequestSerializer
        serializer = serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get('reason')

        try:
            review = action_method(
                review_id=str(review_id),
                actor=request.user,
                reason=reason
            )
            return Response({"status": review.status}, status=status.HTTP_200_OK)
        except (ProductReview.DoesNotExist, ShopReview.DoesNotExist):
            return Response({"detail": "Review not found."}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            msg = e.messages[0] if hasattr(e, 'messages') else str(e)
            return Response({"detail": msg}, status=status.HTTP_400_BAD_REQUEST)


class HideProductReviewView(BaseReviewModerationView):
    @extend_schema(request=ModerateReviewRequestSerializer)
    def post(self, request, review_id):
        return self._execute_moderation(request, review_id, ReviewModerationService.hide_product_review)

class RemoveProductReviewView(BaseReviewModerationView):
    @extend_schema(request=ModerateReviewRequestSerializer)
    def post(self, request, review_id):
        return self._execute_moderation(request, review_id, ReviewModerationService.remove_product_review)

class RestoreProductReviewView(BaseReviewModerationView):
    @extend_schema(request=RestoreReviewRequestSerializer)
    def post(self, request, review_id):
        return self._execute_moderation(request, review_id, ReviewModerationService.restore_product_review, require_reason=False)


class HideShopReviewView(BaseReviewModerationView):
    @extend_schema(request=ModerateReviewRequestSerializer)
    def post(self, request, review_id):
        return self._execute_moderation(request, review_id, ReviewModerationService.hide_shop_review)

class RemoveShopReviewView(BaseReviewModerationView):
    @extend_schema(request=ModerateReviewRequestSerializer)
    def post(self, request, review_id):
        return self._execute_moderation(request, review_id, ReviewModerationService.remove_shop_review)

class RestoreShopReviewView(BaseReviewModerationView):
    @extend_schema(request=RestoreReviewRequestSerializer)
    def post(self, request, review_id):
        return self._execute_moderation(request, review_id, ReviewModerationService.restore_shop_review, require_reason=False)
