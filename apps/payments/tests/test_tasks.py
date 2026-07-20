from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
import uuid

from apps.orders.models import Order
from apps.payments.models import Payment
from apps.payments.tasks import expire_pending_payments_task

User = get_user_model()

class PaymentTasksTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="test@example.com", password="password")
        self.order = Order.objects.create(
            user=self.user,
            subtotal=10, grand_total=10,
            status=Order.OrderStatus.PENDING,
            shipping_address={}
        )
        
        self.fresh_payment = Payment.objects.create(
            order=self.order,
            amount=10,
            provider=Payment.Provider.STRIPE,
            status=Payment.PaymentStatus.PENDING,
            idempotency_key=uuid.uuid4()
        )
        
        self.stale_payment = Payment.objects.create(
            order=self.order,
            amount=10,
            provider=Payment.Provider.STRIPE,
            status=Payment.PaymentStatus.PENDING,
            idempotency_key=uuid.uuid4()
        )
        Payment.objects.filter(id=self.stale_payment.id).update(
            created_at=timezone.now() - timedelta(minutes=45)
        )

    def test_expire_pending_payments_task(self):
        expire_pending_payments_task()
        
        self.fresh_payment.refresh_from_db()
        self.stale_payment.refresh_from_db()
        
        self.assertEqual(self.fresh_payment.status, Payment.PaymentStatus.PENDING)
        self.assertEqual(self.stale_payment.status, Payment.PaymentStatus.FAILED)
        self.assertEqual(self.stale_payment.failure_reason, "Payment timed out.")
