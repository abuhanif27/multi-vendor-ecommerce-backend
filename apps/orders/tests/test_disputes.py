from django.test import TransactionTestCase
from django.utils import timezone
from apps.orders.models import Order, VendorOrder, OrderItem, Dispute, DisputeStatus, ResolutionOutcome
from apps.orders.services.disputes import DisputeService
from apps.shops.models import Shop, Product, ProductVariant
from apps.catalog.models import Category
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from apps.notifications.events import EventBus
from apps.orders.events import DisputeOpenedEvent, DisputeEscalatedEvent, DisputeResolvedEvent
from decimal import Decimal

User = get_user_model()

class DisputeServiceTests(TransactionTestCase):
    def setUp(self):
        EventBus.clear()
        
        self.user = User.objects.create_user(email="buyer@example.com", password="password")
        self.vendor = User.objects.create_user(email="vendor@example.com", password="password")
        self.admin = User.objects.create_user(email="admin@example.com", password="password")
        self.shop = Shop.objects.create(name="Test Shop", owner=self.vendor, status=Shop.ShopStatus.APPROVED)
        self.category = Category.objects.create(name="Electronics", slug="electronics")
        self.product = Product.objects.create(name="Product", shop=self.shop, category=self.category)
        self.variant = ProductVariant.objects.create(product=self.product, sku="SKU-1", price=Decimal('10.00'))
        
        self.order = Order.objects.create(user=self.user, shipping_address={}, grand_total=Decimal('20.00'))
        self.vendor_order = VendorOrder.objects.create(
            order=self.order, shop=self.shop, vendor_total=Decimal('20.00'), status=VendorOrder.FulfillmentStatus.DELIVERED
        )
        self.order_item = OrderItem.objects.create(
            vendor_order=self.vendor_order, variant=self.variant, product_name="Product",
            sku="SKU-1", unit_price=Decimal('10.00'), quantity=2, item_total=Decimal('20.00')
        )
        
        self.events = []
        EventBus.subscribe(DisputeOpenedEvent, lambda e: self.events.append(e))
        EventBus.subscribe(DisputeEscalatedEvent, lambda e: self.events.append(e))
        EventBus.subscribe(DisputeResolvedEvent, lambda e: self.events.append(e))

    def test_open_dispute_success(self):
        dispute = DisputeService.open_dispute(
            vendor_order_id=self.vendor_order.id,
            reason="Item did not match description"
        )
        
        self.assertEqual(dispute.status, DisputeStatus.OPEN)
        self.assertTrue(any(isinstance(e, DisputeOpenedEvent) for e in self.events))

    def test_open_dispute_not_delivered(self):
        self.vendor_order.status = VendorOrder.FulfillmentStatus.SHIPPED
        self.vendor_order.save()
        
        with self.assertRaises(ValidationError):
            DisputeService.open_dispute(
                vendor_order_id=self.vendor_order.id,
                reason="Never received"
            )

    def test_escalate_dispute(self):
        dispute = Dispute.objects.create(vendor_order=self.vendor_order, reason="Test", status=DisputeStatus.OPEN)
        
        DisputeService.escalate_dispute(dispute.id, self.user)
        dispute.refresh_from_db()
        
        self.assertEqual(dispute.status, DisputeStatus.ESCALATED)
        self.assertTrue(any(isinstance(e, DisputeEscalatedEvent) for e in self.events))

    def test_resolve_dispute(self):
        dispute = Dispute.objects.create(vendor_order=self.vendor_order, reason="Test", status=DisputeStatus.ESCALATED)
        
        DisputeService.resolve_dispute(
            dispute_id=dispute.id,
            actor=self.admin,
            outcome=ResolutionOutcome.CUSTOMER_FAVOUR,
            resolution_notes="Refund ordered"
        )
        dispute.refresh_from_db()
        
        self.assertEqual(dispute.status, DisputeStatus.RESOLVED)
        self.assertEqual(dispute.outcome, ResolutionOutcome.CUSTOMER_FAVOUR)
        self.assertTrue(any(isinstance(e, DisputeResolvedEvent) for e in self.events))
