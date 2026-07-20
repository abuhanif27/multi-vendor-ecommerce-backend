from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from apps.common.permissions import IsVendor
from apps.shipping.models import Shipment, Courier
from apps.shipping.serializers import (
    ShipmentReadSerializer,
    ShipmentCourierAssignSerializer,
    ShipmentStatusUpdateSerializer
)
from apps.shipping.services.shipping import ShippingService

class BuyerShipmentListAPIView(generics.ListAPIView):
    """
    GET: List shipments for a specific parent order belonging to the buyer.
    """
    serializer_class = ShipmentReadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        order_id = self.request.query_params.get('order_id')
        if not order_id:
            raise ValidationError({"order_id": "This query parameter is required."})
            
        return Shipment.objects.filter(
            vendor_order__order_id=order_id,
            vendor_order__order__user=self.request.user
        ).select_related('courier').prefetch_related('tracking_events')

class VendorShipmentDetailAPIView(generics.RetrieveAPIView):
    """
    GET: View shipment details (Vendor only).
    """
    serializer_class = ShipmentReadSerializer
    permission_classes = [IsVendor]
    queryset = Shipment.objects.all()

    def get_object(self):
        obj = super().get_object()
        if obj.vendor_order.shop.owner != self.request.user:
            raise PermissionDenied("You do not have permission to view this shipment.")
        return obj

class VendorShipmentAssignCourierAPIView(generics.GenericAPIView):
    """
    POST: Assign courier and tracking number.
    """
    permission_classes = [IsVendor]
    serializer_class = ShipmentCourierAssignSerializer
    
    @extend_schema(responses={200: ShipmentReadSerializer})
    def post(self, request, pk, *args, **kwargs):
        shipment = get_object_or_404(Shipment, pk=pk)
        
        if shipment.vendor_order.shop.owner != request.user:
            raise PermissionDenied("You do not have permission to modify this shipment.")
            
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        courier_id = serializer.validated_data['courier_id']
        tracking_number = serializer.validated_data['tracking_number']
        
        courier = get_object_or_404(Courier, id=courier_id)
        
        try:
            shipment = ShippingService.assign_courier(shipment.id, courier, tracking_number)
        except DjangoValidationError as e:
            raise ValidationError({"detail": e.messages})
            
        return Response(ShipmentReadSerializer(shipment).data, status=status.HTTP_200_OK)

class VendorShipmentStatusUpdateAPIView(generics.GenericAPIView):
    """
    PATCH: Update physical tracking state of the shipment.
    """
    permission_classes = [IsVendor]
    serializer_class = ShipmentStatusUpdateSerializer
    
    @extend_schema(responses={200: ShipmentReadSerializer})
    def patch(self, request, pk, *args, **kwargs):
        shipment = get_object_or_404(Shipment, pk=pk)
        
        if shipment.vendor_order.shop.owner != request.user:
            raise PermissionDenied("You do not have permission to modify this shipment.")
            
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            shipment = ShippingService.update_shipment_status(
                shipment_id=shipment.id,
                new_status=serializer.validated_data['status'],
                location=serializer.validated_data.get('location', ""),
                description=serializer.validated_data.get('description', "")
            )
        except DjangoValidationError as e:
            raise ValidationError({"detail": e.messages})
            
        return Response(ShipmentReadSerializer(shipment).data, status=status.HTTP_200_OK)
