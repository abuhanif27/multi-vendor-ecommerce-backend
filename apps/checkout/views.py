from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError

from apps.checkout.services.checkout import CheckoutService
from apps.checkout.serializers import CheckoutSummarySerializer, CheckoutProcessSerializer

class CheckoutAPIView(APIView):
    """
    GET: Retrieve checkout summary and warnings.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            summary_data = CheckoutService.get_checkout_summary(request.user)
        except DjangoValidationError as e:
            raise ValidationError({"detail": e.messages})
            
        serializer = CheckoutSummarySerializer(summary_data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """
        POST: Process checkout.
        """
        serializer = CheckoutProcessSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            dto = CheckoutService.process_checkout(
                user=request.user,
                shipping_address=serializer.validated_data["shipping_address"],
                billing_address=serializer.validated_data.get("billing_address")
            )
        except DjangoValidationError as e:
            raise ValidationError({"detail": e.messages})
            
        # Return success with DTO placeholder (in a real scenario, returning Order ID)
        return Response({
            "detail": "Checkout processed successfully.",
            "cart_id": dto["cart_id"],
            "grand_total": dto["financials"]["grand_total"],
        }, status=status.HTTP_200_OK)
