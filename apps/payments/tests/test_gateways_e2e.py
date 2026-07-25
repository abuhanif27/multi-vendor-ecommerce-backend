import unittest
from unittest.mock import patch, MagicMock
from decimal import Decimal
import uuid

from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.payments.services.payment import PaymentService
from apps.payments.models import Payment, Refund
from apps.orders.models import Order
from apps.shops.models import Shop
# from apps.users.models import User
User = get_user_model()

class MultiGatewayE2ETests(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='shopper@example.com',
            password='password123',
            first_name='Test',
            last_name='Shopper'
        )
        self.shop = Shop.objects.create(
            name='Gateway Test Shop',
            slug='gateway-test-shop',
            owner=self.user
        )
        self.order_stripe = Order.objects.create(
            user=self.user,
            grand_total=Decimal('100.00'),
            status=Order.OrderStatus.PENDING,
            shipping_address={'address': '123 Test St'}
        )
        self.order_ssl = Order.objects.create(
            user=self.user,
            grand_total=Decimal('250.50'),
            status=Order.OrderStatus.PENDING,
            shipping_address={'address': '456 Test Ave'}
        )

    @patch('stripe.PaymentIntent.create')
    def test_stripe_e2e_flow(self, mock_create):
        # 1. Initialize Stripe
        mock_intent = MagicMock()
        mock_intent.client_secret = 'pi_123_secret'
        mock_intent.id = 'pi_123'
        mock_create.return_value = mock_intent

        gateway_res = PaymentService.initialize_payment(
            order_id=self.order_stripe.id,
            provider='STRIPE'
        )
        
        self.assertEqual(gateway_res['url']['client_secret'], 'pi_123_secret')
        payment = Payment.objects.get(order=self.order_stripe)
        self.assertEqual(payment.provider, 'STRIPE')
        self.assertEqual(payment.status, Payment.PaymentStatus.PENDING)

        # 2. Simulate Webhook Success
        PaymentService.process_webhook_success(
            payment_id=payment.id,
            provider_reference='pi_123',
            raw_metadata={'event_id': 'evt_123', 'bank_tran_id': 'pi_123'},
            verified_amount=Decimal('100.00')
        )

        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.PaymentStatus.CAPTURED)
        self.assertEqual(payment.provider_reference, 'pi_123')
        self.order_stripe.refresh_from_db()
        self.assertEqual(self.order_stripe.status, Order.OrderStatus.PAID)

        # 3. Simulate Idempotent Webhook Delivery (Duplicate)
        PaymentService.process_webhook_success(
            payment_id=payment.id,
            provider_reference='pi_123',
            raw_metadata={'event_id': 'evt_123'},
            verified_amount=Decimal('100.00')
        )
        # Should not raise any errors, and status remains CAPTURED
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.PaymentStatus.CAPTURED)

        # 4. Refund Payment
        from apps.payments.models import RefundStatus
        with patch('stripe.Refund.create') as mock_refund:
            mock_ref = MagicMock()
            mock_ref.id = 're_123'
            mock_ref.status = 'succeeded'
            mock_refund.return_value = mock_ref

            refund = PaymentService.process_refund(
                payment_id=payment.id,
                amount=Decimal('100.00'),
                reason_code="Test Refund"
            )
            self.assertEqual(refund.status, RefundStatus.SUCCEEDED)
            
            payment.refresh_from_db()
            refund.refresh_from_db()
            self.assertEqual(refund.status, RefundStatus.SUCCEEDED)

    @patch('apps.payments.gateways.sslcommerz.SSLCommerzGateway.initialize_payment')
    def test_sslcommerz_e2e_flow(self, mock_init):
        # 1. Initialize SSLCommerz
        mock_init.return_value = 'https://sandbox.sslcommerz.com/testurl'

        gateway_res = PaymentService.initialize_payment(
            order_id=self.order_ssl.id,
            provider='SSLCOMMERZ'
        )
        
        self.assertEqual(gateway_res['url'], 'https://sandbox.sslcommerz.com/testurl')
        payment = Payment.objects.get(order=self.order_ssl)
        self.assertEqual(payment.provider, 'SSLCOMMERZ')
        self.assertEqual(payment.status, Payment.PaymentStatus.PENDING)

        # 2. Simulate Webhook Failure
        PaymentService.process_webhook_failure(
            payment_id=payment.id,
            failure_reason='Customer cancelled',
            raw_metadata={'error': 'cancelled'}
        )
        
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.PaymentStatus.FAILED)
        self.order_ssl.refresh_from_db()
        self.assertEqual(self.order_ssl.status, Order.OrderStatus.CANCELLED)

        # 3. Simulate Idempotent Failure (Duplicate)
        PaymentService.process_webhook_failure(
            payment_id=payment.id,
            failure_reason='Customer cancelled',
            raw_metadata={'error': 'cancelled'}
        )
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.PaymentStatus.FAILED)

    def test_invalid_provider(self):
        with self.assertRaises(NotImplementedError):
            PaymentService.initialize_payment(
                order_id=self.order_ssl.id,
                provider='UNKNOWN_GATEWAY'
            )
