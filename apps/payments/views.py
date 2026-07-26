from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError

from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from apps.payments.serializers import PaymentInitializationSerializer
from apps.payments.services.payment import PaymentService

class PaymentInitializeAPIView(APIView):
    """
    POST: Initialize a payment for an order.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Initialize Payment",
        description="Initialize a payment for an order using a specified provider.",
        request=PaymentInitializationSerializer,
        responses={
            200: OpenApiResponse(description="Payment initialized", response=dict),
            400: OpenApiResponse(description="Bad Request or not implemented")
        },
        tags=['Payments']
    )

    def post(self, request, *args, **kwargs):
        serializer = PaymentInitializationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            gateway_response = PaymentService.initialize_payment(
                order_id=serializer.validated_data["order_id"],
                provider=serializer.validated_data["provider"]
            )
        except DjangoValidationError as e:
            raise ValidationError({"detail": e.messages})
        except NotImplementedError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response(gateway_response, status=status.HTTP_200_OK)


class StripeWebhookAPIView(APIView):
    """
    POST: Example Stripe Webhook endpoint.
    No authentication required, relies on HMAC signature verification.
    """
    permission_classes = []

    @extend_schema(
        summary="Stripe Webhook (Deprecated/Old)",
        description="Old webhook endpoint for Stripe.",
        exclude=True
    )

    def post(self, request, *args, **kwargs):
        # 1. Verify Signature (Delegate to Gateway)
        # gateway = StripeGateway()
        # payload = gateway.verify_webhook(request)
        
        # 2. Process logic based on payload
        # if payload["status"] == "CAPTURED":
        #     PaymentService.process_webhook_success(
        #         payment_id=payload["payment_id"],
        #         provider_reference=payload["provider_reference"],
        #         raw_metadata=payload["raw_metadata"]
        #     )
        
        # ALWAYS return 200 OK immediately to prevent gateway retries
        return Response(status=status.HTTP_200_OK)
