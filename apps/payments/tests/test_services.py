import uuid
from decimal import Decimal
from django.test import TransactionTestCase
from django.utils import timezone
from apps.payments.models import Payment, Refund, RefundStatus, RefundReason
from apps.payments.services.payment import PaymentService
from apps.orders.models import Order, VendorOrder
from apps.shops.models import Shop
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from apps.notifications.events import EventBus
from apps.payments.events import PaymentRefundedEvent
import unittest.mock as mock

User = get_user_model()

class PaymentServiceRefundTests(TransactionTestCase):
    def setUp(self):
        EventBus.clear()
        
        self.user = User.objects.create_user(email="buyer@example.com", password="password")
        self.vendor = User.objects.create_user(email="vendor@example.com", password="password")
        self.shop = Shop.objects.create(name="Test Shop", owner=self.vendor, status=Shop.ShopStatus.APPROVED)
        
        self.order = Order.objects.create(user=self.user, shipping_address={}, billing_address={}, grand_total=Decimal('100.00'), status=Order.OrderStatus.PAID)
        self.vendor_order = VendorOrder.objects.create(
            order=self.order, shop=self.shop, vendor_total=Decimal('100.00'), status=VendorOrder.FulfillmentStatus.PROCESSING
        )
        
        self.payment = Payment.objects.create(
            order=self.order,
            provider=Payment.Provider.COD,
            amount=Decimal('100.00'),
            status=Payment.PaymentStatus.CAPTURED,
            idempotency_key=uuid.uuid4()
        )
        
        self.events = []
        EventBus.subscribe(PaymentRefundedEvent, lambda e: self.events.append(e))

    def test_process_refund_success(self):
        refund = PaymentService.process_refund(
            payment_id=self.payment.id,
            amount=Decimal('50.00'),
            reason_code=RefundReason.CUSTOMER_REQUEST,
            vendor_order_id=self.vendor_order.id
        )
        
        self.assertEqual(refund.status, RefundStatus.SUCCEEDED)
        self.assertEqual(refund.amount, Decimal('50.00'))
        self.assertEqual(refund.reason_code, RefundReason.CUSTOMER_REQUEST)
        
        self.assertEqual(len(self.events), 1)
        self.assertIsInstance(self.events[0], PaymentRefundedEvent)
        self.assertEqual(self.events[0].amount, '50.00')

    def test_process_refund_exceeds_amount(self):
        with self.assertRaisesMessage(ValidationError, "Refund amount exceeds available payment balance."):
            PaymentService.process_refund(
                payment_id=self.payment.id,
                amount=Decimal('150.00'),
                reason_code=RefundReason.CUSTOMER_REQUEST
            )

    def test_process_refund_partial_then_full(self):
        PaymentService.process_refund(
            payment_id=self.payment.id,
            amount=Decimal('50.00'),
            reason_code=RefundReason.CUSTOMER_REQUEST
        )
        
        # Second refund should succeed
        PaymentService.process_refund(
            payment_id=self.payment.id,
            amount=Decimal('50.00'),
            reason_code=RefundReason.CUSTOMER_REQUEST
        )
        
        # Third refund should fail
        with self.assertRaisesMessage(ValidationError, "Refund amount exceeds available payment balance."):
            PaymentService.process_refund(
                payment_id=self.payment.id,
                amount=Decimal('1.00'),
                reason_code=RefundReason.CUSTOMER_REQUEST
            )
