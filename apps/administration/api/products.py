from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from django.core.exceptions import ValidationError, PermissionDenied
from apps.shops.models import Product
from apps.administration.services.product_moderation import ProductModerationService
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers

class ApproveProductRequestSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True)

class ApproveProductView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        request=ApproveProductRequestSerializer,
        responses={200: inline_serializer("ApproveProductResponse", fields={"status": serializers.CharField()})}
    )
    def post(self, request, product_id):
        serializer = ApproveProductRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get('reason')

        try:
            product = ProductModerationService.approve_product(
                product_id=str(product_id),
                actor=request.user,
                reason=reason
            )
            return Response({"status": product.status}, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            msg = e.messages[0] if hasattr(e, 'messages') else str(e)
            return Response({"detail": msg}, status=status.HTTP_400_BAD_REQUEST)


class RejectProductRequestSerializer(serializers.Serializer):
    reason = serializers.CharField(required=True, allow_blank=False)

class RejectProductView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        request=RejectProductRequestSerializer,
        responses={200: inline_serializer("RejectProductResponse", fields={"status": serializers.CharField()})}
    )
    def post(self, request, product_id):
        serializer = RejectProductRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get('reason')

        try:
            product = ProductModerationService.reject_product(
                product_id=str(product_id),
                actor=request.user,
                reason=reason
            )
            return Response({"status": product.status}, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            msg = e.messages[0] if hasattr(e, 'messages') else str(e)
            return Response({"detail": msg}, status=status.HTTP_400_BAD_REQUEST)


class SuspendProductRequestSerializer(serializers.Serializer):
    reason = serializers.CharField(required=True, allow_blank=False)

class SuspendProductView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        request=SuspendProductRequestSerializer,
        responses={200: inline_serializer("SuspendProductResponse", fields={"status": serializers.CharField()})}
    )
    def post(self, request, product_id):
        serializer = SuspendProductRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get('reason')

        try:
            product = ProductModerationService.suspend_product(
                product_id=str(product_id),
                actor=request.user,
                reason=reason
            )
            return Response({"status": product.status}, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            msg = e.messages[0] if hasattr(e, 'messages') else str(e)
            return Response({"detail": msg}, status=status.HTTP_400_BAD_REQUEST)


class RestoreProductRequestSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True)

class RestoreProductView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        request=RestoreProductRequestSerializer,
        responses={200: inline_serializer("RestoreProductResponse", fields={"status": serializers.CharField()})}
    )
    def post(self, request, product_id):
        serializer = RestoreProductRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get('reason')

        try:
            product = ProductModerationService.restore_product(
                product_id=str(product_id),
                actor=request.user,
                reason=reason
            )
            return Response({"status": product.status}, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            msg = e.messages[0] if hasattr(e, 'messages') else str(e)
            return Response({"detail": msg}, status=status.HTTP_400_BAD_REQUEST)
