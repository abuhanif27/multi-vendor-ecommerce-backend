import unittest
from unittest.mock import patch, MagicMock
from decimal import Decimal
import stripe
from django.test import TestCase
from django.conf import settings

from apps.payments.gateways.stripe import StripeGateway
from apps.payments.exceptions import (
    PaymentGatewayUnavailable,
    PaymentValidationFailed,
    PaymentInitializationFailed,
    PaymentRefundFailed
)

class StripeGatewayTests(TestCase):
    def setUp(self):
        self.gateway = StripeGateway()

    @patch('stripe.PaymentIntent.create')
    def test_initialize_payment_success(self, mock_create):
        # Setup mock
        mock_intent = MagicMock()
        mock_intent.client_secret = 'pi_123_secret_456'
        mock_intent.id = 'pi_123'
        mock_create.return_value = mock_intent

        # Execute
        result = self.gateway.initialize_payment(
            payment_id='pay_001',
            amount=Decimal('10.50'),
            currency='USD',
            customer_info={'email': 'test@example.com'},
            return_url_base='http://localhost:8000'
        )

        # Assert
        self.assertEqual(result['client_secret'], 'pi_123_secret_456')
        self.assertEqual(result['payment_intent_id'], 'pi_123')
        self.assertEqual(result['publishable_key'], settings.STRIPE_PUBLISHABLE_KEY)
        
        # Verify Stripe API called with cents
        mock_create.assert_called_once_with(
            amount=1050,
            currency='usd',
            metadata={'payment_id': 'pay_001'},
            receipt_email='test@example.com'
        )

    @patch('stripe.PaymentIntent.create')
    def test_initialize_payment_failure(self, mock_create):
        # Setup mock to raise a Stripe error
        mock_create.side_effect = stripe.error.CardError("Card declined", param="number", code="card_declined")

        # Execute and Assert
        with self.assertRaises(PaymentInitializationFailed):
            self.gateway.initialize_payment(
                payment_id='pay_001',
                amount=Decimal('10.50'),
                currency='USD',
                customer_info={},
                return_url_base='http://localhost:8000'
            )

    @patch('stripe.PaymentIntent.retrieve')
    def test_validate_payment_success(self, mock_retrieve):
        # Setup mock
        mock_intent = MagicMock()
        mock_intent.status = 'succeeded'
        mock_intent.amount_received = 1050
        mock_intent.currency = 'usd'
        mock_intent.metadata = {'payment_id': 'pay_001'}
        mock_intent.id = 'pi_123'
        mock_intent.latest_charge = 'ch_123'
        mock_intent.payment_method = 'pm_123'
        mock_retrieve.return_value = mock_intent

        # Execute
        result = self.gateway.validate_payment({'payment_intent_id': 'pi_123'})

        # Assert
        self.assertTrue(result['valid'])
        self.assertEqual(result['amount'], Decimal('10.50'))
        self.assertEqual(result['currency'], 'USD')
        self.assertEqual(result['tran_id'], 'pay_001')
        self.assertEqual(result['raw_metadata']['payment_intent_id'], 'pi_123')

    @patch('stripe.PaymentIntent.retrieve')
    def test_validate_payment_failed(self, mock_retrieve):
        # Setup mock
        mock_intent = MagicMock()
        mock_intent.status = 'requires_payment_method'
        mock_retrieve.return_value = mock_intent

        # Execute and Assert
        with self.assertRaises(PaymentValidationFailed):
            self.gateway.validate_payment({'payment_intent_id': 'pi_123'})

    @patch('stripe.Refund.create')
    def test_refund_payment_success(self, mock_refund_create):
        # Setup mock
        mock_refund = MagicMock()
        mock_refund.status = 'succeeded'
        mock_refund.id = 're_123'
        mock_refund_create.return_value = mock_refund

        # Execute
        result = self.gateway.refund_payment(
            refund_id='ref_001',
            payment_id='pay_001',
            amount=Decimal('10.50'),
            bank_tran_id='pi_123'
        )

        # Assert
        self.assertTrue(result['success'])
        self.assertEqual(result['raw_metadata']['refund_id'], 're_123')
        mock_refund_create.assert_called_once_with(
            payment_intent='pi_123',
            amount=1050,
            metadata={'refund_id': 'ref_001', 'payment_id': 'pay_001'}
        )

    @patch('stripe.Refund.create')
    def test_refund_payment_failure(self, mock_refund_create):
        # Setup mock
        mock_refund = MagicMock()
        mock_refund.status = 'failed'
        mock_refund_create.return_value = mock_refund

        # Execute and Assert
        with self.assertRaises(PaymentRefundFailed):
            self.gateway.refund_payment(
                refund_id='ref_001',
                payment_id='pay_001',
                amount=Decimal('10.50'),
                bank_tran_id='pi_123'
            )
