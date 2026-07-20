from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

from apps.orders.models import Order
from apps.orders.tasks import expire_abandoned_orders_task

User = get_user_model()

class OrderTasksTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="test@example.com", password="password")
        
        # Fresh order (should not be cancelled)
        self.fresh_order = Order.objects.create(
            user=self.user,
            subtotal=10, grand_total=10,
            status=Order.OrderStatus.PENDING,
            shipping_address={}
        )
        
        # Stale order (should be cancelled)
        self.stale_order = Order.objects.create(
            user=self.user,
            subtotal=10, grand_total=10,
            status=Order.OrderStatus.PENDING,
            shipping_address={}
        )
        # Manually backdate created_at
        Order.objects.filter(id=self.stale_order.id).update(
            created_at=timezone.now() - timedelta(minutes=45)
        )
        
        # Paid stale order (should NOT be cancelled)
        self.paid_stale_order = Order.objects.create(
            user=self.user,
            subtotal=10, grand_total=10,
            status=Order.OrderStatus.PAID,
            shipping_address={}
        )
        Order.objects.filter(id=self.paid_stale_order.id).update(
            created_at=timezone.now() - timedelta(minutes=45)
        )

    def test_expire_abandoned_orders_task(self):
        expire_abandoned_orders_task()
        
        self.fresh_order.refresh_from_db()
        self.stale_order.refresh_from_db()
        self.paid_stale_order.refresh_from_db()
        
        self.assertEqual(self.fresh_order.status, Order.OrderStatus.PENDING)
        self.assertEqual(self.stale_order.status, Order.OrderStatus.CANCELLED)
        self.assertEqual(self.paid_stale_order.status, Order.OrderStatus.PAID)
