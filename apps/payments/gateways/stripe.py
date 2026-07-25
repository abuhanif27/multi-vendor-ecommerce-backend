import logging
import stripe
from decimal import Decimal
from django.conf import settings
from apps.payments.gateways.base import PaymentGateway
from apps.payments.exceptions import (
    PaymentGatewayUnavailable,
    PaymentValidationFailed,
    PaymentInitializationFailed,
    PaymentRefundFailed
)

logger = logging.getLogger(__name__)

class StripeGateway(PaymentGateway):
    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        self.publishable_key = settings.STRIPE_PUBLISHABLE_KEY
        self.is_test_mode = getattr(settings, 'STRIPE_TEST_MODE', True)

    def initialize_payment(self, payment_id: str, amount: Decimal, currency: str, customer_info: dict, return_url_base: str) -> dict:
        """
        Creates a Stripe PaymentIntent and returns the client secret and intent ID.
        """
        try:
            # Stripe expects amounts in cents for most currencies
            # E.g., $10.00 is 1000 cents.
            amount_in_cents = int(amount * 100)
            
            logger.info(f"Stripe Init Request: payment_id={payment_id}, amount={amount}")
            intent = stripe.PaymentIntent.create(
                amount=amount_in_cents,
                currency=currency.lower(),
                metadata={'payment_id': payment_id},
                receipt_email=customer_info.get('email')
            )
            
            return {
                'client_secret': intent.client_secret,
                'payment_intent_id': intent.id,
                'publishable_key': self.publishable_key
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe Init Failed: {str(e)}")
            raise PaymentInitializationFailed(f"Gateway error: {str(e)}") from e
        except Exception as e:
            logger.error(f"Stripe connection error during init: {str(e)}")
            raise PaymentGatewayUnavailable("Failed to connect to Stripe") from e

    def validate_payment(self, payload: dict) -> dict:
        """
        Validates the webhook event directly utilizing Stripe's SDK Signature verification
        but this method might be used for manual checking of an intent if needed.
        Typically, webhooks handle this in Stripe.
        """
        payment_intent_id = payload.get('payment_intent_id')
        if not payment_intent_id:
            raise PaymentValidationFailed("Missing payment_intent_id in payload")
            
        try:
            logger.info(f"Stripe Validation Request: intent_id={payment_intent_id}")
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            if intent.status != 'succeeded':
                logger.error(f"Stripe Validation Failed: status={intent.status}")
                raise PaymentValidationFailed(f"Transaction validation failed with status {intent.status}")
                
            return {
                'valid': True,
                'amount': Decimal(intent.amount_received) / 100,
                'currency': intent.currency.upper(),
                'tran_id': intent.metadata.get('payment_id'),
                'raw_metadata': {
                    'payment_intent_id': intent.id,
                    'latest_charge': intent.latest_charge,
                    'payment_method': intent.payment_method
                }
            }
        except PaymentValidationFailed:
            raise
        except stripe.error.StripeError as e:
            logger.error(f"Stripe Validation Failed: {str(e)}")
            raise PaymentValidationFailed(f"Gateway validation failed: {str(e)}") from e
        except Exception as e:
            logger.error(f"Stripe connection error during validation: {str(e)}")
            raise PaymentGatewayUnavailable("Failed to connect to Stripe validation API") from e

    def refund_payment(self, refund_id: str, payment_id: str, amount: Decimal, bank_tran_id: str = None) -> dict:
        """
        bank_tran_id corresponds to the Stripe PaymentIntent ID or Charge ID.
        """
        if not bank_tran_id:
            raise PaymentRefundFailed("bank_tran_id (payment_intent_id) is required for Stripe refund")
            
        try:
            amount_in_cents = int(amount * 100)
            logger.info(f"Stripe Refund Request: intent_id={bank_tran_id}, amount={amount}")
            
            refund = stripe.Refund.create(
                payment_intent=bank_tran_id,
                amount=amount_in_cents,
                metadata={
                    'refund_id': refund_id,
                    'payment_id': payment_id
                }
            )
            
            if refund.status == 'succeeded':
                return {
                    'success': True,
                    'raw_metadata': {
                        'refund_id': refund.id,
                        'status': refund.status
                    }
                }
            elif refund.status == 'pending':
                return {
                    'success': True,  # Treat pending as success internally for async
                    'raw_metadata': {
                        'refund_id': refund.id,
                        'status': refund.status
                    }
                }
            else:
                logger.error(f"Stripe Refund Failed with status: {refund.status}")
                raise PaymentRefundFailed(f"Gateway refund failed with status: {refund.status}")
                
        except PaymentRefundFailed:
            raise
        except stripe.error.StripeError as e:
            logger.error(f"Stripe Refund Failed: {str(e)}")
            raise PaymentRefundFailed(f"Gateway refund failed: {str(e)}") from e
        except Exception as e:
            logger.error(f"Stripe connection error during refund: {str(e)}")
            raise PaymentGatewayUnavailable("Failed to connect to Stripe refund API") from e
