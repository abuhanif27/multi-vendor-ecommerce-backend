from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from django.core.exceptions import ValidationError, PermissionDenied
from apps.shops.models import Shop
from apps.administration.services.vendor import VendorAdministrationService
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers

class ApproveVendorRequestSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True)

class ApproveVendorView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        request=ApproveVendorRequestSerializer,
        responses={200: inline_serializer("ApproveVendorResponse", fields={"status": serializers.CharField()})}
    )
    def post(self, request, shop_id):
        # We enforce specific permissions in the service, but can also enforce here.
        # It's safer to enforce in service to keep the service decoupled,
        # but the request itself requires IsAdminUser.
        
        serializer = ApproveVendorRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get('reason')

        try:
            shop = VendorAdministrationService.approve_vendor(
                shop_id=str(shop_id),
                actor=request.user,
                reason=reason
            )
            return Response({"status": shop.status}, status=status.HTTP_200_OK)
        except Shop.DoesNotExist:
            return Response({"detail": "Shop not found."}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            msg = e.messages[0] if hasattr(e, 'messages') else str(e)
            return Response({"detail": msg}, status=status.HTTP_400_BAD_REQUEST)

class SuspendVendorRequestSerializer(serializers.Serializer):
    reason = serializers.CharField(required=True, allow_blank=False)

class SuspendVendorView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        request=SuspendVendorRequestSerializer,
        responses={200: inline_serializer("SuspendVendorResponse", fields={"status": serializers.CharField()})}
    )
    def post(self, request, shop_id):
        serializer = SuspendVendorRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get('reason')

        try:
            shop = VendorAdministrationService.suspend_vendor(
                shop_id=str(shop_id),
                actor=request.user,
                reason=reason
            )
            return Response({"status": shop.status}, status=status.HTTP_200_OK)
        except Shop.DoesNotExist:
            return Response({"detail": "Shop not found."}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            msg = e.messages[0] if hasattr(e, 'messages') else str(e)
            return Response({"detail": msg}, status=status.HTTP_400_BAD_REQUEST)

class RestoreVendorRequestSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True)

class RestoreVendorView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        request=RestoreVendorRequestSerializer,
        responses={200: inline_serializer("RestoreVendorResponse", fields={"status": serializers.CharField()})}
    )
    def post(self, request, shop_id):
        serializer = RestoreVendorRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get('reason')

        try:
            shop = VendorAdministrationService.restore_vendor(
                shop_id=str(shop_id),
                actor=request.user,
                reason=reason
            )
            return Response({"status": shop.status}, status=status.HTTP_200_OK)
        except Shop.DoesNotExist:
            return Response({"detail": "Shop not found."}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            msg = e.messages[0] if hasattr(e, 'messages') else str(e)
            return Response({"detail": msg}, status=status.HTTP_400_BAD_REQUEST)
