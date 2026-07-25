import uuid
from decimal import Decimal
from unittest.mock import patch, Mock
from django.test import TransactionTestCase
from django.conf import settings
from apps.orders.models import Order
from apps.payments.models import Payment, Refund, RefundStatus
from apps.payments.services.payment import PaymentService
from apps.payments.gateways.sslcommerz import SSLCommerzGateway
from apps.payments.gateways.registry import gateway_registry
from apps.payments.exceptions import PaymentInitializationFailed, PaymentValidationFailed
from django.contrib.auth import get_user_model

User = get_user_model()

class SSLCommerzGatewayTests(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="buyer@example.com", password="password")
        self.order = Order.objects.create(
            user=self.user,
            shipping_address={"phone": "123456"},
            grand_total=Decimal('100.00'),
            status=Order.OrderStatus.PENDING
        )
        
        # Ensure gateway is registered
        if 'SSLCOMMERZ' not in gateway_registry._gateways:
            gateway_registry.register('SSLCOMMERZ', SSLCommerzGateway())

    @patch('apps.payments.gateways.sslcommerz.requests.post')
    def test_initialize_payment_success(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "SUCCESS",
            "GatewayPageURL": "https://sandbox.sslcommerz.com/gw/session",
            "sessionkey": "session123"
        }
        mock_post.return_value = mock_response
        
        response = PaymentService.initialize_payment(self.order.id, 'SSLCOMMERZ', 'http://localhost:8000')
        
        self.assertIn("url", response)
        self.assertEqual(response["url"], "https://sandbox.sslcommerz.com/gw/session")
        
        payment = Payment.objects.get(order=self.order)
        self.assertEqual(payment.status, Payment.PaymentStatus.PENDING)
        self.assertEqual(payment.provider, 'SSLCOMMERZ')

    @patch('apps.payments.gateways.sslcommerz.requests.post')
    def test_initialize_payment_failure(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "FAILED",
            "failedreason": "Invalid credentials"
        }
        mock_post.return_value = mock_response
        
        with self.assertRaises(PaymentInitializationFailed):
            PaymentService.initialize_payment(self.order.id, 'SSLCOMMERZ', 'http://localhost:8000')

    @patch('apps.payments.gateways.sslcommerz.requests.get')
    def test_webhook_validation_success(self, mock_get):
        payment = Payment.objects.create(
            order=self.order,
            provider='SSLCOMMERZ',
            amount=Decimal('100.00'),
            idempotency_key=uuid.uuid4()
        )
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "VALID",
            "amount": "100.00",
            "currency": "BDT",
            "tran_id": str(payment.id),
            "val_id": "val123",
            "bank_tran_id": "bank123",
            "card_type": "VISA"
        }
        mock_get.return_value = mock_response
        
        gateway = gateway_registry.get('SSLCOMMERZ')
        payload = {"tran_id": str(payment.id), "val_id": "val123"}
        
        validation_result = gateway.validate_payment(payload)
        
        self.assertTrue(validation_result['valid'])
        self.assertEqual(validation_result['amount'], Decimal('100.00'))
        
        # Test full webhook process via service
        PaymentService.process_webhook_success(
            payment_id=str(payment.id),
            provider_reference=validation_result['tran_id'],
            raw_metadata=validation_result['raw_metadata']
        )
        
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.PaymentStatus.CAPTURED)
        self.assertEqual(payment.raw_metadata['val_id'], "val123")

    @patch('apps.payments.gateways.sslcommerz.requests.get')
    def test_refund_payment_success(self, mock_get):
        payment = Payment.objects.create(
            order=self.order,
            provider='SSLCOMMERZ',
            amount=Decimal('100.00'),
            status=Payment.PaymentStatus.CAPTURED,
            idempotency_key=uuid.uuid4(),
            raw_metadata={"bank_tran_id": "bank123"}
        )
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "success",
            "refund_ref_id": "ref123"
        }
        mock_get.return_value = mock_response
        
        refund = PaymentService.process_refund(
            payment_id=str(payment.id),
            amount=Decimal('50.00'),
            reason_code="CUSTOMER_REQUEST"
        )
        
        self.assertEqual(refund.status, RefundStatus.SUCCEEDED)
        self.assertEqual(refund.provider_reference, "ref123")
