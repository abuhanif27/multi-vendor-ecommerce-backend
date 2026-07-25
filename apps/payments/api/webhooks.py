from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import logging
from apps.payments.services.payment import PaymentService
from apps.payments.gateways.registry import gateway_registry
from apps.payments.exceptions import PaymentGatewayError, PaymentValidationFailed

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class SSLCommerzWebhookView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, action):
        payload = request.POST.dict()
        tran_id = payload.get('tran_id')
        
        if not tran_id:
            logger.error("SSLCommerz webhook missing tran_id")
            return Response({"error": "Missing tran_id"}, status=status.HTTP_400_BAD_REQUEST)

        gateway = gateway_registry.get('SSLCOMMERZ')

        if action in ['success', 'ipn']:
            try:
                validation_result = gateway.validate_payment(payload)
                # Ensure the verified amount matches the requested amount?
                # Actually, validation_result contains verified amount, we can pass it or check inside process_webhook_success
                # We'll trust process_webhook_success to fetch the payment and compare the amount.
                # Actually, let's just pass raw_metadata from validation_result
                PaymentService.process_webhook_success(
                    payment_id=tran_id,
                    provider_reference=validation_result['tran_id'],
                    raw_metadata=validation_result['raw_metadata'],
                    verified_amount=validation_result['amount']
                )
                # Successful processing
                return Response({"status": "success"}, status=status.HTTP_200_OK)
            except PaymentValidationFailed as e:
                logger.error(f"Validation failed for {tran_id}: {e}")
                PaymentService.process_webhook_failure(
                    payment_id=tran_id,
                    failure_reason=str(e),
                    raw_metadata=payload
                )
                return Response({"error": "Validation failed"}, status=status.HTTP_400_BAD_REQUEST)
            except PaymentGatewayError as e:
                logger.error(f"Gateway error for {tran_id}: {e}")
                return Response({"error": "Gateway error"}, status=status.HTTP_502_BAD_GATEWAY)
            except Exception as e:
                logger.error(f"Unexpected error for {tran_id}: {e}")
                return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        elif action in ['fail', 'cancel']:
            reason = payload.get('error', 'Customer cancelled or failed payment')
            try:
                PaymentService.process_webhook_failure(
                    payment_id=tran_id,
                    failure_reason=reason,
                    raw_metadata=payload
                )
                return Response({"status": "processed"}, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"Failed to process {action} for {tran_id}: {e}")
                return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)
