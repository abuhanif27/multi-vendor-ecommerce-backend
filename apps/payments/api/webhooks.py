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

from drf_spectacular.utils import extend_schema
@method_decorator(csrf_exempt, name='dispatch')
class SSLCommerzWebhookView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        summary="SSLCommerz Webhook",
        description="Receives payment updates from SSLCommerz.",
        exclude=True
    )

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

@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        summary="Stripe Webhook",
        description="Receives payment updates from Stripe.",
        exclude=True
    )

    def post(self, request):
        import stripe
        from django.conf import settings
        
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        webhook_secret = settings.STRIPE_WEBHOOK_SECRET

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        except ValueError as e:
            # Invalid payload
            logger.error(f"Stripe Webhook Error: Invalid payload")
            return Response({"error": "Invalid payload"}, status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            logger.error(f"Stripe Webhook Error: Invalid signature")
            return Response({"error": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Stripe Webhook Error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Handle the event
        gateway = gateway_registry.get('STRIPE')
        
        if event.type == 'payment_intent.succeeded':
            payment_intent = event.data.object
            payment_id = payment_intent.metadata.get('payment_id')
            
            if not payment_id:
                logger.warning("Stripe payment_intent.succeeded missing payment_id in metadata.")
                return Response({"status": "ignored"}, status=status.HTTP_200_OK)

            try:
                # Validation happens through the webhook signature inherently, 
                # but we use our adapter for consistent formatting if needed, 
                # or just parse here.
                verified_amount = Decimal(payment_intent.amount_received) / 100
                
                PaymentService.process_webhook_success(
                    payment_id=payment_id,
                    provider_reference=payment_intent.id,
                    raw_metadata={
                        'payment_intent_id': payment_intent.id,
                        'event_id': event.id
                    },
                    verified_amount=verified_amount
                )
            except Exception as e:
                logger.error(f"Error processing Stripe success for {payment_id}: {e}")
                # We return 200 on business errors inside process_webhook_success 
                # to prevent Stripe from retrying infinitely if it's our logic fault,
                # but for concurrency it might raise. Actually, PaymentService handles idempotency.
                # Returning 200 is safest for duplicate deliveries.

        elif event.type == 'payment_intent.payment_failed':
            payment_intent = event.data.object
            payment_id = payment_intent.metadata.get('payment_id')
            
            if payment_id:
                failure_reason = "Payment failed"
                if payment_intent.last_payment_error:
                    failure_reason = payment_intent.last_payment_error.message
                    
                PaymentService.process_webhook_failure(
                    payment_id=payment_id,
                    failure_reason=failure_reason,
                    raw_metadata={'payment_intent_id': payment_intent.id, 'event_id': event.id}
                )

        elif event.type == 'charge.refunded':
            # Refunds are normally synchronous via our refund API, but Stripe may refund out-of-band.
            # Usually handled by the webhook. We might not need to do anything here if our Domain handles it synchronously.
            pass

        return Response({"status": "success"}, status=status.HTTP_200_OK)
