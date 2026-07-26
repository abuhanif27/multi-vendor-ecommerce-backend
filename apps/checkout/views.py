from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError

from apps.checkout.services.checkout import CheckoutService
from apps.checkout.serializers import CheckoutSummarySerializer, CheckoutProcessSerializer

from drf_spectacular.utils import extend_schema, OpenApiResponse
class CheckoutAPIView(APIView):
    """
    GET: Retrieve checkout summary and warnings.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get Checkout Summary",
        description="Retrieve checkout summary including cart items, warnings, and totals.",
        responses={200: CheckoutSummarySerializer},
        tags=['Checkout']
    )
    def get(self, request, *args, **kwargs):
        try:
            summary_data = CheckoutService.get_checkout_summary(request.user)
        except DjangoValidationError as e:
            raise ValidationError({"detail": e.messages})
            
        serializer = CheckoutSummarySerializer(summary_data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Process Checkout",
        description="Submit shipping/billing addresses to process checkout and create an order.",
        request=CheckoutProcessSerializer,
        responses={
            200: OpenApiResponse(description="Order created successfully"),
            400: OpenApiResponse(description="Validation error")
        },
        tags=['Checkout']
    )
    def post(self, request, *args, **kwargs):
        serializer = CheckoutProcessSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            order = CheckoutService.process_checkout(
                user=request.user,
                shipping_address=serializer.validated_data["shipping_address"],
                billing_address=serializer.validated_data.get("billing_address")
            )
        except DjangoValidationError as e:
            raise ValidationError({"detail": e.messages})
            
        return Response({
            "detail": "Checkout processed successfully.",
            "order_id": str(order.id),
            "grand_total": order.grand_total,
        }, status=status.HTTP_200_OK)
